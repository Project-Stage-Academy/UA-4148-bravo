def get_field_value(serializer, data, field_name):
    """
    Gets value from validated_data first, instance second, else None.
    """
    if field_name in data:
        return data[field_name]
    if hasattr(serializer, 'instance') and serializer.instance is not None:
        return getattr(serializer.instance, field_name, None)
    return None
