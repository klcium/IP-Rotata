#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def confirm(default_choice="n"):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    """
    answer = None
    while answer not in ["y", "n"]:
        if default_choice == "n":
            answer = input("Continue [y/N]? ").lower()
        else:
            answer = input("Continue [Y/n]? ").lower()
        if len(answer) == 0:
            answer = default_choice
    return answer == "y"

def select_option_int():
    """Ask user to input an integer"""
    answer = None
    while type(answer) is not int:
        answer = input("Please select an Id: ")
        try:
            answer = int(answer)
        except ValueError:
            print("Please send an integer ! >:(")
    return answer