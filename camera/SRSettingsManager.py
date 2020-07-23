from configparser import ConfigParser

class SRSettingsManager(ConfigParser):
    LOGIN_SECTION = "Login"
    CAMERA_SECTION = "Camera"
    DEFAULT_INI_FILE_LOCATION = "settings/settings.ini"

    def __init__(self, file_location=DEFAULT_INI_FILE_LOCATION):
        super().__init__()
        self.INI_FILE_LOCATION = file_location
        self.setting_type_map = dict()

        if not self.read(file_location):
            raise Exception(f" * ERROR: settings.ini not found in directory: \"{file_location}\"")

        self._setup()

    def _setup(self):
        self._register_setting("password_hash", self.LOGIN_SECTION)
        self._register_setting("password_salt", self.LOGIN_SECTION)
        self._register_setting("save_clips_enabled", self.CAMERA_SECTION, settingtype=bool)
        self._register_setting("movement_box_enabled", self.CAMERA_SECTION, settingtype=bool)
        self._register_setting("minimum_clip_length_secs", self.CAMERA_SECTION, settingtype=float)
        self._register_setting("no_movement_wait_time_secs", self.CAMERA_SECTION, settingtype=float)

    def set(self, section, key, value):
        try:
            self.setting_type_map[key](value)
        except:
            return
        
        valuetype = type(value)
        if valuetype is bool or valuetype is int or valuetype is float:
            value = str(value)

        super().set(section, key, value)

        with open(self.INI_FILE_LOCATION, "w") as config:
            self.write(config)

    def settingtype(settingname):
        return 

    def _register_setting(self, settingname, settingsection, settingtype=str):
        self.setting_type_map[settingname] = settingtype

        getter = self.get
        if settingtype is bool:
            getter = self.getboolean
        elif settingtype is int:
            getter = self.getint
        elif settingtype is float:
            getter = self.getfloat

        settingproperty = property(lambda self: getter(settingsection, settingname), lambda self, value: self.set(settingsection, settingname, value))
        setattr(SRSettingsManager, settingname, settingproperty)
