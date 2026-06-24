# -*- coding: utf-8 -*-
"""Install a prebuilt Skin Variables shortcut set from the setup wizard."""

import json
import sys
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


BASE_PROPERTY = "SkinVariables.ShortcutsNode"
DEST_BASE = "special://profile/addon_data/script.skinvariables/nodes"
SOURCE_BASE = "special://skin/shortcuts/prebuilt"
HOME_WINDOW = 10000
PRESERVE_WIDGETS_CHOICE = "existing-widgets"

THEMES = {
    "bright": {
        "focus": "",
        "gradient": "",
        "disable_monochrome": False,
        "revert_selected": False,
        "dialog": "",
        "background": "special://skin/extras/backgrounds/blur/purple_blur.jpg",
    },
    "miami": {
        "focus": "ffe91e63",
        "gradient": "ffb635e5",
        "disable_monochrome": True,
        "revert_selected": True,
        "dialog": "",
        "background": "special://skin/extras/backgrounds/blur/purple_blur.jpg",
    },
    "aqua": {
        "focus": "ff0091ea",
        "gradient": "ff00bfa5",
        "disable_monochrome": True,
        "revert_selected": True,
        "dialog": "Green",
        "background": "special://skin/extras/backgrounds/blur/green_blur.jpg",
    },
    "sunset": {
        "focus": "fff4511e",
        "gradient": "ffe91e63",
        "disable_monochrome": True,
        "revert_selected": True,
        "dialog": "Blush",
        "background": "special://skin/extras/backgrounds/blur/pink_blur.jpg",
    },
    "slate": {
        "focus": "ff0091ea",
        "gradient": "ff0091ea",
        "disable_monochrome": False,
        "revert_selected": True,
        "dialog": "Slate",
        "background": "special://skin/extras/backgrounds/blur/slate_blur.jpg",
    },
    "midnight": {
        "focus": "ff5528a8",
        "gradient": "ff5528a8",
        "disable_monochrome": False,
        "revert_selected": True,
        "dialog": "Coal",
        "background": "special://skin/extras/backgrounds/blur/coal_blur.jpg",
    },
}


def builtin(command):
    xbmc.executebuiltin(command)


def skin_reset(name):
    builtin(f"Skin.Reset({name})")


def skin_set_bool(name):
    builtin(f"Skin.SetBool({name})")


def skin_set_string(name, value):
    builtin(f"Skin.SetString({name},{value})")


def set_or_reset_string(name, value):
    if value:
        skin_set_string(name, value)
    else:
        skin_reset(name)


def set_or_reset_bool(name, enabled):
    if enabled:
        skin_set_bool(name)
    else:
        skin_reset(name)


def adaptive_dialog_enabled():
    return xbmc.getCondVisibility(
        "Skin.HasSetting(TMDbHelper.EnableBlur) + String.IsEmpty(Skin.String(Background.ArtworkStyle))"
    )


def parse_args(argv):
    params = {}
    for arg in argv:
        if "=" not in arg:
            params[arg] = "true"
            continue
        key, value = arg.split("=", 1)
        params[key] = value
    return params


def read_text(path):
    handle = xbmcvfs.File(path)
    try:
        return handle.read()
    finally:
        handle.close()


def write_text(path, content):
    handle = xbmcvfs.File(path, "w")
    try:
        return handle.write(content)
    finally:
        handle.close()


def confirm_overwrite(skin, source_dir):
    skinvariables_addon = xbmcaddon.Addon("script.skinvariables")
    filename = skinvariables_addon.getLocalizedString(32073).format(skin=skin)
    content = skinvariables_addon.getLocalizedString(32074).format(folder=source_dir)
    message = "{}\n{}\n\n{}".format(
        skinvariables_addon.getLocalizedString(32072).format(filename=filename, content=content),
        skinvariables_addon.getLocalizedString(32043),
        "Customized widgets, menu items, lists, and shortcuts will be replaced."
    )
    return xbmcgui.Dialog().yesno(
        skinvariables_addon.getLocalizedString(32075),
        message
    )


def install_prebuilt(choice, skin):
    source_dir = f"{SOURCE_BASE}/{choice}/"
    dest_dir = f"{DEST_BASE}/{skin}/"

    _, files = xbmcvfs.listdir(source_dir)
    files = [name for name in files if name.endswith(".json")]
    if not files:
        xbmcgui.Dialog().ok("Prebuilt widgets", f"No prebuilt shortcut files found for {choice}.")
        return False

    existing_files = [f"{dest_dir}{filename}" for filename in files if xbmcvfs.exists(f"{dest_dir}{filename}")]
    first_run_setup = xbmc.getCondVisibility("Skin.HasSetting(Wizard.FirstRunSetup)")
    if existing_files and not first_run_setup and not confirm_overwrite(skin, source_dir):
        return True

    xbmcvfs.mkdirs(dest_dir)
    window = xbmcgui.Window(10000)

    for filename in files:
        source = f"{source_dir}{filename}"
        dest = f"{dest_dir}{filename}"
        content = read_text(source)

        # Match script.skinvariables' in-memory shortcut cache as well as the file.
        meta = json.loads(content)
        window.setProperty(f"{BASE_PROPERTY}.{skin}-{filename}", json.dumps(meta))
        write_text(dest, json.dumps(meta, indent=4))

    window.setProperty(f"{BASE_PROPERTY}.Reload", str(time.time()))
    return True


def apply_theme(theme):
    config = THEMES.get(theme)
    if not config:
        return

    set_or_reset_string("focuscolor.name", config["focus"])
    set_or_reset_string("gradientcolor.name", config["gradient"])
    set_or_reset_bool("DisableMonochromeHighlight", config["disable_monochrome"])
    set_or_reset_bool("RevertSelectedText", config["revert_selected"])

    if adaptive_dialog_enabled():
        skin_set_string("Background.DialogImage", "Adaptive")
    else:
        set_or_reset_string("Background.DialogImage", config["dialog"])

    skin_set_string("Background.Image", config["background"])
    builtin(f"RunScript(plugin.video.themoviedb.helper,blur_image={config['background']},prefix=SimpleBackground)")


def apply_dialog(dialog, theme):
    if not dialog:
        return

    builtin("RunScript(script.skinvariables,get_jsonrpc=Settings.SetSettingValue,setting=lookandfeel.skincolors,value=SKINDEFAULT)")

    if dialog == "adaptive":
        skin_set_string("Background.DialogImage", "Adaptive")
    elif dialog == "standard":
        if theme == "aqua":
            skin_set_string("Background.DialogImage", "Green")
        elif theme == "sunset":
            skin_set_string("Background.DialogImage", "Blush")
        else:
            skin_reset("Background.DialogImage")
    elif dialog == "slate":
        skin_set_string("Background.DialogImage", "Slate")
    elif dialog == "coal":
        skin_set_string("Background.DialogImage", "Coal")


def apply_layout(layout):
    if not layout:
        return

    skin_reset("Hub.Home.ReplaceWindow")
    if layout == "advanced":
        skin_reset("Hub.Home.DisableSubmenu")
        skin_reset("Hub.Home.EnableDetailedInformation")
    elif layout == "detailed":
        skin_set_bool("Hub.Home.DisableSubmenu")
        skin_set_bool("Hub.Home.EnableDetailedInformation")
    elif layout == "basic":
        skin_set_bool("Hub.Home.DisableSubmenu")
        skin_reset("Hub.Home.EnableDetailedInformation")


def apply_pending_wizard_choices(window):
    theme = window.getProperty("Wizard.Theme")
    dialog = window.getProperty("Wizard.Dialog")
    layout = window.getProperty("Wizard.Layout")
    if layout == "advanced" and xbmc.getCondVisibility("Skin.HasSetting(Wizard.FirstRunSetup)"):
        layout = "detailed"

    apply_theme(theme)
    apply_dialog(dialog, theme)
    apply_layout(layout)


def clear_wizard_properties():
    for name in ("WizardStep", "WizardStepPrevious", "Wizard.Theme", "Wizard.Dialog", "Wizard.Layout"):
        builtin(f"ClearProperty({name},Home)")


def rebuild_skinvariables(timestamp):
    skin_set_string("Shortcuts.RebuildDateTime", timestamp)
    builtin(
        "RunScript(script.skinvariables,"
        "run_executebuiltin=special://skin/shortcuts/skinvariables-build-templates.json,"
        "use_rules=True)"
    )
    builtin(
        "RunScript(script.skinvariables,"
        "run_executebuiltin=special://skin/shortcuts/skinvariables-build-colortemplates.json,"
        "use_rules=True,"
        "reload=Home)"
    )


def main():
    params = parse_args(sys.argv[1:])
    choice = params.get("v")
    skin = params.get("skin")
    close = params.get("close", "false").lower() == "true"

    if not choice or not skin:
        xbmcgui.Dialog().ok("Prebuilt widgets", "Missing prebuilt widget choice or skin folder.")
        return

    if choice != PRESERVE_WIDGETS_CHOICE and not install_prebuilt(choice, skin):
        return

    window = xbmcgui.Window(HOME_WINDOW)
    apply_pending_wizard_choices(window)

    timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
    skin_set_bool("Wizard.FirstRun")
    skin_reset("Wizard.FirstRunSetup")
    clear_wizard_properties()
    builtin("CancelAlarm(openwizard,true)")
    if close:
        builtin("PreviousMenu")
        xbmc.sleep(100)

    rebuild_skinvariables(timestamp)


if __name__ == "__main__":
    main()
