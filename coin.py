

class Coin:
    def __init__(self, name):
        self.name = name



class Polis(Coin):
    def __init__(self, config):
        Coin.__init__(self, "polis")
        self.coin_name="polis"
        self.default_wallet_dir = config["default_wallet_dir"]
        self.default_dir = config["default_dir"]
        self.version_to_upload = config["version_to_upload"]
        self.scripts = config["scripts"]
        self.cli = config["cli"]
        self.daemon = config["daemon"]
        self.vps = config["vps"]
        self.addnode= config["addnode"]
        if "sentinel_git" in config :
            self.sentinel_git = config["sentinel_git"]
        else:
            self.sentinel_git = ""

