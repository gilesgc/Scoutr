from configparser import ConfigParser

class GCSettingsManager(ConfigParser):
    LOGIN_SECTION = "Login"
    CAMERA_SECTION = "Camera"
    DEFAULT_INI_FILE_LOCATION = "settings/settings.ini"

    def __init__(self, file_location=DEFAULT_INI_FILE_LOCATION):
        super().__init__()
        self.INI_FILE_LOCATION = file_location

        if not self.read(file_location):
            raise Exception(f" * ERROR: settings.ini not found in directory: \"{file_location}\"")

        self._setup()

    def _setup(self):
        self._register_setting("password_hash", self.LOGIN_SECTION)
        self._register_setting("password_salt", self.LOGIN_SECTION)
        self._register_setting("save_clips_enabled", self.CAMERA_SECTION, settingtype=bool)
        self._register_setting("movement_square_enabled", self.CAMERA_SECTION, settingtype=bool)

    def set(self, section, key, value):
        valuetype = type(value)
        if valuetype is bool or valuetype is int or valuetype is float:
            value = str(value)

        super().set(section, key, value)

        with open(self.INI_FILE_LOCATION, "w") as config:
            self.write(config)

    def _register_setting(self, settingname, settingsection, settingtype=str):
        getter = self.get

        if settingtype is bool:
            getter = self.getboolean
        elif settingtype is int:
            getter = self.getint
        elif settingtype is float:
            getter = self.getfloat

        settingproperty = property(lambda self: getter(settingsection, settingname), lambda self, value: self.set(settingsection, settingname, value))
        setattr(GCSettingsManager, settingname, settingproperty)

    """@property
    def password_hash(self):
        return self.get(self.LOGIN_SECTION, "password_hash")

    @password_hash.setter
    def password_hash(self, pwhash):
        self.set(self.LOGIN_SECTION, "password_hash", pwhash)

    @property
    def save_clips_enabled(self):
        return self.getboolean(self.CAMERA_SECTION, "save_clips_enabled")

    @save_clips_enabled.setter
    def save_clips_enabled(self, enabled: bool):
        self.set(self.CAMERA_SECTION, "save_clips_enabled", str(enabled))

    @property
    def movement_square_enabled(self):
        return self.getboolean(self.CAMERA_SECTION, "movement_square_enabled")

    @movement_square_enabled.setter
    def movement_square_enabled(self, enabled: bool):
        self.set(self.CAMERA_SECTION, "movement_square_enabled", str(enabled))"""