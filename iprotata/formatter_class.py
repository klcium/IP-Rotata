import argparse

class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _format_action_invocation(self, action):
        if action.option_strings:
            return ''.join(action.option_strings)
        else:
            return self._format_args(action, action.dest)