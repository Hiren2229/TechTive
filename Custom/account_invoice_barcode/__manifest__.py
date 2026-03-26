# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice Barcode',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 6,
    'author': 'ErpMstar Solutions',
    'summary': 'Allows you to allocate barcode in every account invoice.',
    'description': "Allows you to allocate barcode in every account invoice.",
    'depends': ['account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        # 'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 15,
    'currency': 'EUR',
}
