class UploadError(Exception):
    def __init__(self, arg):
        self.msg = arg
        