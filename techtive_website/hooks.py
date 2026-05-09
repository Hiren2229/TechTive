# -*- coding: utf-8 -*-
import base64
import logging

from odoo import SUPERUSER_ID, api
from odoo.modules import get_module_resource

_logger = logging.getLogger(__name__)


def post_init_hook(cr, _registry):
    """Apply bundled TechTive logo and favicon to the default website."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    website = env.ref("website.default_website", raise_if_not_found=False)
    if not website:
        return
    logo_path = get_module_resource(
        "techtive_website", "static", "src", "img", "techtive_logo.png"
    )
    fav_path = get_module_resource(
        "techtive_website", "static", "src", "img", "techtive_favicon.png"
    )
    vals = {}
    if logo_path:
        try:
            with open(logo_path, "rb") as f:
                vals["logo"] = base64.b64encode(f.read())
        except OSError as err:
            _logger.warning("TechTive website: could not read logo: %s", err)
    if fav_path:
        try:
            with open(fav_path, "rb") as f:
                vals["favicon"] = base64.b64encode(f.read())
        except OSError as err:
            _logger.warning("TechTive website: could not read favicon: %s", err)
    if vals:
        website.write(vals)
