import os
from json import dump, load
import schedule


class Config:

    config_path = os.path.join(os.getcwd(), "config")

    @staticmethod
    def config_exists(config):
        return os.path.exists(os.path.join(Config.config_path, f"{config}.json"))

    @staticmethod
    def create_config(config):
        with open(os.path.join(Config.config_path, f"{config}.json"), "w") as f:
            dump({}, f, indent=4)

    @staticmethod
    def set_name(name):
        with open(os.path.join(os.getcwd(), "config", "setup.json"), "r") as f:
            config = load(f)
            config["name"] = name
            with open(os.path.join(os.getcwd(), "config", "setup.json"), "w") as f:
                dump(config, f, indent=4)

    @staticmethod
    def get_config(config):
        with open(os.path.join(Config.config_path, f"{config}.json"), "r") as f:
            config = load(f)
            return config

    @staticmethod
    def set_alarm(time, days:str|None=None):
        with open(os.path.join(Config.config_path, "task.json"), "r") as f:
            tasks = load(f)
        with open(os.path.join(Config.config_path, "task.json"), "w") as f:
            if days:
                for day in days:
                    getattr(schedule.every(), day.lower()).at(time.strftime("%H:%M:%S")).do(lambda: print("Alarm!")) # TODO ADD ALARM FUNCTION
                tasks["recurring_alarms"].append({"time": time, "days": days})
                dump(tasks, f, indent=4)
            else:
                tasks["alarms"]["unnamed"].append({"time": time})
                dump(tasks, f, indent=4)

    @staticmethod
    def get_alarms():
        with open(os.path.join(Config.config_path, "task.json"), "r") as f:
            tasks = load(f)
            return tasks["alarms"]

    @staticmethod
    def get_recurring_alarms():
        with open(os.path.join(Config.config_path, "task.json"), "r") as f:
            tasks = load(f)
            return tasks["recurring_alarms"]

    @staticmethod
    def remove_alarm(index):
        with open(os.path.join(Config.config_path, "task.json"), "r") as f:
            config = load(f)
            config["alarms"].remove(index)
            with open(os.path.join(Config.config_path, "task.json"), "w") as f:
                dump(config, f, indent=4)
