import os
from abc import ABC, abstractmethod
from typing import Literal


class HookCliDisplay(ABC):
    """Implementation for printing hook information to the terminal"""

    @abstractmethod
    def will_run_hook(self, event_key: str, time: int): ...
    @abstractmethod
    def will_run_hook_tick(self): ...
    @abstractmethod
    def after_will_run_hook(self): ...
    @abstractmethod
    def system_info(self, msg: str): ...
    @abstractmethod
    def system_warn(self, msg: str): ...
    @abstractmethod
    def hook_execution_begin(self, event_key: str, name: str): ...
    @abstractmethod
    def hook_execution_end(self, event_key: str, name: str, success: bool | Literal["warn"]): ...


class DefaultHookCliDisplay(HookCliDisplay):
    def will_run_hook(self, event_key: str, time: int):
        info_msg = (
            "Riptide Hooks: Will run "
            + event_key
            + " hooks in "
            + str(time)
            + " seconds. Hit CTRL+C to skip running hooks"
        )
        print(info_msg, end="")

    def will_run_hook_tick(self):
        print(".", end="")

    def after_will_run_hook(self):
        cols = os.get_terminal_size().columns
        print("\r" + " " * cols + "\r", end="")

    def system_info(self, msg: str):
        print("Riptide Hooks: " + msg)

    def system_warn(self, msg: str):
        print("Riptide Warning: " + msg)

    def hook_execution_begin(self, event_key: str, name: str):
        print("Riptide Hooks: Running " + event_key + " Hook: " + name + "...")

    def hook_execution_end(self, event_key: str, name: str, success: bool | Literal["warn"]):
        if success == "warn":
            print("Riptide Warning: Hook failed. Continuing...")
        elif not success:
            print("Riptide Hooks: Hook failed.")
        else:
            print("Riptide Hooks: Hook " + name + " finished.")
