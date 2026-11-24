class ErrorCodes:
    MALFORMED_DATA = "malformed_data"
    PERMISSION_DENIED = "permission_denied"
    OBJ_NOT_EDITABLE = "not_editable"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    DOCUMENT_NOT_FOUND = "document_not_found"
    NOT_FOUND = "not_found"
    NOT_ALLOWED = "not_allowed"
    INVALID_CREDENTIALS = "invalid_credentials"


class UserMessages:
    MALFORMED_DATA = "اطلاعات وارد شده معتبر نیست"
    PERMISSION_DENIED = "شما اجازه دسترسی به این قسمت را ندارید"
    OBJ_NOT_EDITABLE = "امکان ویرایش وجود ندارد"
    FILE_TOO_LARGE = "حجم فایل بیشتر از حد مجاز است"
    UNSUPPORTED_FILE_TYPE = "فرمت فایل پشتیبانی نمی‌شود"
    DOCUMENT_NOT_FOUND = "سند مورد نظر یافت نشد"
    EMPTY_INPUT_FIELD = "این فیلد الزامی است"
    NOT_FOUND = "موردی یافت نشد"
    NOT_ALLOWED = "انجام این عملیات مجاز نیست"
    INVALID_CREDENTIALS = "نام کاربری یا رمز عبور اشتباه است"
    USERNAME_TAKEN = "نام کاربری قبلاً انتخاب شده است"
    EMAIL_TAKEN = "ایمیل قبلاً استفاده شده است"

class ValidationPatterns:
    VALIDATE_EMAIL = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
