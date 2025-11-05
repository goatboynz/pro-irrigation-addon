# Add-on Icon

The Pro-Irrigation add-on requires an icon file for display in the Home Assistant add-on store.

## Requirements

- **Filename**: `icon.png`
- **Location**: Root directory of the add-on
- **Size**: 256x256 pixels (recommended)
- **Format**: PNG with transparency support
- **Content**: Should represent irrigation/sprinkler system

## Suggested Icon

Use the Material Design Icon `mdi:sprinkler-variant` as inspiration, or create a custom icon showing:
- A sprinkler head
- Water droplets
- Irrigation system elements
- Green/blue color scheme

## Creating the Icon

You can:
1. Use an icon generator service
2. Create a custom icon in a graphics editor
3. Use a free icon from icon libraries (ensure license compatibility)
4. Export the MDI icon as PNG at 256x256

## Temporary Solution

Until a custom icon is created, Home Assistant will use the default add-on icon. The `panel_icon: mdi:sprinkler-variant` in config.yaml will be used for the sidebar.
