# -*- coding: utf-8 -*-
{
    "name": "TechTive Website",
    "summary": "TechTive branding, theme colors, and website assets for Odoo Website",
    "version": "16.0.1.0.0",
    "category": "Website/Website",
    "author": "TechTive",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [],
    "post_init_hook": "post_init_hook",
    "assets": {
        "web._assets_primary_variables": [
            "techtive_website/static/src/scss/techtive_user_values.scss",
            "techtive_website/static/src/scss/techtive_user_color_palette.scss",
            "techtive_website/static/src/scss/techtive_user_theme_color_palette.scss",
        ],
    },
    "installable": True,
    "application": False,
}
