import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

logger = logging.getLogger(__name__)


class BaseValidatedModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that runs model full_clean() validation
    and logs creation and update events.
    """

    def _validate_and_log(self, serializer, action):
        if action == 'create':
            # Build the instance in memory, but do not persist yet
            instance = serializer.Meta.model(
                **serializer.validated_data, user=self.request.user
            )
        else:  # update
            instance = serializer.instance
            for attr, value in serializer.validated_data.items():
                setattr(instance, attr, value)

        # Run Django model validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            logger.warning(f"Validation error during {action}: {e}")
            raise DRFValidationError(e.message_dict)

        # Save only after successful validation
        instance.save()

        logger.info(f"Startup {action}d: {instance}")
        return instance

    def perform_create(self, serializer):
        self._validate_and_log(serializer, "create")

    def perform_update(self, serializer):
        self._validate_and_log(serializer, "update")


