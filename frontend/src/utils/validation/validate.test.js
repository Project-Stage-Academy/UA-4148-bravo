import { Validator } from './validate';
import { describe, expect, test } from '@jest/globals';

describe('validate company name', () => {
    test('should be null when "Company"', () => {
        expect(Validator.validateField('companyName', 'Company', {})).toBeNull();
    });

    test('should be not null when "C"', () => {
        expect(Validator.validateField('companyName', 'C', {})).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('companyName', '', {})).not.toBeNull();
    });
});

describe('validate email', () => {
    test('should be null when "emailemail@email.com"', () => {
        expect(Validator.validateField('email', 'emailemail@email.com', {})).toBeNull();
    });

    test('should be not null when "emailemail@email."', () => {
        expect(Validator.validateField('email', 'emailemail@email.', {})).not.toBeNull();
    });

    test('should be not null when "emailemail@email"', () => {
        expect(Validator.validateField('email', 'emailemail@email', {})).not.toBeNull();
    });

    test('should be not null when "emailemail@"', () => {
        expect(Validator.validateField('email', 'emailemail@', {})).not.toBeNull();
    });

    test('should be not null when "@email.com"', () => {
        expect(Validator.validateField('email', '@email.com', {})).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('email', '', {})).not.toBeNull();
    });
});

describe('validate password', () => {
    test('should be null when "Password123"', () => {
        expect(Validator.validateField('password', 'Password123', {})).toBeNull();
    });

    test('should be not null when "Password"', () => {
        expect(Validator.validateField('password', 'Password', {})).not.toBeNull();
    });

    test('should be not null when "password123"', () => {
        expect(Validator.validateField('password', 'password123', {})).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('password', '', {})).not.toBeNull();
    });
});

describe('validate confirm password', () => {
    const data = { password: 'Password123' };

    test('should be null when "Password123" is equal to password', () => {
        expect(Validator.validateField('confirmPassword', 'Password123', data)).toBeNull();
    });

    test('should be not null when "Password" is not equal to password', () => {
        expect(Validator.validateField('confirmPassword', 'Password', data)).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('confirmPassword', '', data)).not.toBeNull();
    });
});

describe('validate first name', () => {
    test('should be null when "Ivan"', () => {
        expect(Validator.validateField('firstName', 'Ivan', {})).toBeNull();
    });

    test('should be not null when "Ivan1"', () => {
        expect(Validator.validateField('firstName', 'Ivan1', {})).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('firstName', '', {})).not.toBeNull();
    });
});

describe('validate last name', () => {
    test('should be null when "Superman"', () => {
        expect(Validator.validateField('lastName', 'Superman', {})).toBeNull();
    });

    test('should be not null when "Superman1"', () => {
        expect(Validator.validateField('lastName', 'Superman1', {})).not.toBeNull();
    });

    test('should be not null when ""', () => {
        expect(Validator.validateField('lastName', '', {})).not.toBeNull();
    });
});

describe('validate representation', () => {
    test('should be null when { true, false }', () => {
        const formData = {
            representation: {
                company: true,
                startup: false
            }
        };

        expect(Validator.validateField('representation', formData.representation, formData)).toBeNull();
    });

    test('should be null when { true, true }', () => {
        const formData = {
            representation: {
                company: true,
                startup: true
            }
        };

        expect(Validator.validateField('representation', formData.representation, formData)).toBeNull();
    });

    test('should be not null when { false, false }', () => {
        const formData = {
            representation: {
                company: false,
                startup: false
            }
        };

        expect(Validator.validateField('representation', formData.representation, formData)).not.toBeNull();
    });
});

describe('validate businessType', () => {
    test('should be null when { true, false }', () => {
        const formData = {
            businessType: {
                individual: true,
                legal: false
            }
        };

        expect(Validator.validateField('businessType', formData.businessType, formData)).toBeNull();
    });

    test('should be null when { true, true }', () => {
        const formData = {
            businessType: {
                individual: true,
                legal: true
            }
        };

        expect(Validator.validateField('businessType', formData.businessType, formData)).toBeNull();
    });

    test('should be not null when { false, false }', () => {
        const formData = {
            businessType: {
                individual: false,
                legal: false
            }
        };

        expect(Validator.validateField('businessType', formData.businessType, formData)).not.toBeNull();
    });
});

describe('validate data object', () => {
    test('should be { * : null } when all positive', () => {
        const formData = {
            companyName: "Company",
            email: "emailemail@email.com",
            password: "Password123",
            confirmPassword: "Password123",
            lastName: "Superman",
            firstName: "Ivan",
            representation: {
                company: true,
                startup: false
            },
            businessType: {
                individual: true,
                legal: false
            }
        };

        const expected = {
            companyName: null,
            email: null,
            password: null,
            confirmPassword: null,
            lastName: null,
            firstName: null,
            representation: null,
            businessType: null
        };

        expect(Validator.validate(formData)).toStrictEqual(expected);
    });

    test('should be { * : "error message" } when all negative', () => {
        const formData = {
            companyName: "",
            email: "",
            password: "",
            confirmPassword: "",
            lastName: "",
            firstName: "",
            representation: {
                company: false,
                startup: false
            },
            businessType: {
                individual: false,
                legal: false
            }
        };

        const expected = {
            companyName: Validator.errorZeroLengthMessages["companyName"],
            email: Validator.errorZeroLengthMessages["email"],
            password: Validator.errorZeroLengthMessages["password"],
            confirmPassword: Validator.errorZeroLengthMessages["confirmPassword"],
            lastName: Validator.errorZeroLengthMessages["lastName"],
            firstName: Validator.errorZeroLengthMessages["firstName"],
            representation: Validator.errorZeroLengthMessages["representation"],
            businessType: Validator.errorZeroLengthMessages["businessType"]
        };

        expect(Validator.validate(formData)).toStrictEqual(expected);
    });
});
