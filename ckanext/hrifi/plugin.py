#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# 
#
from logging import getLogger
log = getLogger(__name__)

import os
from pylons import c

from pylons.i18n import _
import ckan.plugins as p

from ckanext.hrifi.authentication.wordpress_auth import WordPressAuthMiddleware
from hri_auth import hri_site_read, no_registering, hri_user_auth
from hri_auth import hri_group_update, hri_group_create, hri_group_delete, hri_group_delete, hri_package_update, hri_package_create, hri_dataset_delete, hri_package_create_rest, hri_package_update_rest, hri_package_show_auth
from hri_auth import hri_package_show_rest

from ckan.lib.base import config

import datetime


class Hrifi(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.ITemplateHelpers)
    
    
    def before_map(self, map):

        wordpress_url = config.get('wordpress_url', 'www.hri.fi')
        if 'http://' not in wordpress_url:
            wordpress_url = 'http://' + wordpress_url

        map.connect('/dataset/copy/{id}', controller='ckanext.hrifi.controllers.hri_package_controller:package', action='copy')
        map.connect('/dataset', controller='ckanext.hrifi.controllers.hri_package_controller:package', action='search')
        map.redirect('/user/login', '/admin')
        map.redirect('/', wordpress_url)
        
        return map
    
    def get_auth_functions(self):
        return {
            # Disable user registration and browsing by denying access.
            'site_read' : hri_site_read,
            # http://stackoverflow.com/questions/18171937/ckan-prevent-user-from-auto-registering 
            'user_create': no_registering,
            # "HRI Harvester" functionality
            'group_update' : hri_group_update,
            'group_create' : hri_group_create,
            'group_delete' : hri_group_delete,            
            'package_update' : hri_package_update,
            'package_create' : hri_package_create,
            'package_delete': hri_dataset_delete,
            'package_create_rest' : hri_package_create_rest,
            'package_update_rest' : hri_package_update_rest,
            'package_show' : hri_package_show_auth,
            # HRI-108: Only sysadmins may view CKAN users.
            'user_list': hri_user_auth,
            'user_show': hri_user_auth
        }
    
    # The "HRI Harvester"    
    # Here we re-route these API actions in order to alter their functionality for harvester users.
    # @TODO Move this to its own plugin
    def get_actions(self):
        return {
            'package_show_rest': hri_package_show_rest
        }
    
    def update_config(self, config):
		# Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        p.toolkit.add_template_directory(config, 'templates')

        # Similarily for the public directory.
        p.toolkit.add_public_directory(config, 'public')

        # Here we add "scripts" and "css" Fanstatic libraries. Warning! 'css' library is apparently taken already...
        p.toolkit.add_resource('fanstatic/scripts/', 'hri-scripts')
        p.toolkit.add_resource('fanstatic/css/', 'hri-css')

    def is_fallback(self):
        return True

    def package_types(self):
        return ['dataset']

    # Add our custom facets' titles here.
    def dataset_facets(self, facets, package_type):

        facets['author'] = _('Author')
        facets['geographic_coverage'] = _('geographic_coverage')

        return facets

    @staticmethod
    def wordpress_url():
        """
        This helper simply returns WordPress URL, as defined in the settings (ckan.ini).
        The URL is used to dynamically craft URLs to the right places (notably in dev and staging environments).
        
        usage: {{ h.wordpress_url() }}
        """
        return config.get('wordpress_url', 'www.hri.fi')

    @staticmethod
    def now(format):
        """
        This helper returns current timestamp with given format.
        
        usage: {{ h.now('%d.%m.%Y') }}
        """
        return datetime.date.today().strftime(format)

    @staticmethod
    def make_facet_inputs(fields):
        """
        Wraps facet selections as a HTML inputs.
        
        usage: {{ h.make_facet_string(facets.fields) }}
        """
        facet_string = ''
        if fields:
         for facet, selections in fields.items():
           for selection in selections:
            facet_string += '<input hidden="hidden" style="display: none;" name="' + facet + '" value="' + selection + '" />'

        return p.toolkit.literal(facet_string)
    
    @staticmethod
    def get_ga_code():
        """
        This helper simply returns Google Analytics code, as defined in the settings (ckan.ini).
        
        usage: {{ h.get_ga_code() }}
        """
        return config.get('google_analytics_code', '')

    @staticmethod
    def solve_localized_value(field_name, locale, extras, default_value):
        """
        This helper looks through extras for a localized value of given field.
        If not found, the default_value given will be returned.
        
        example usage: {{ h.solve_localized_value('notes', locale, pkg.extras, c.pkg_notes_formatted) }}
        """
        field = field_name + "_" + locale

        for extra in extras:
            if extra['key'] == field:
                if extra['value']:
                    return extra['value']
                else:
                    return default_value

        return default_value

    @staticmethod
    def format_notes(data):
        """
        Format notes -field text naturally in regards to line breaks (as it is in the editor).
        
        usage: {{ h.format_notes(h.solve_localized_value('notes', locale, pkg.extras, c.pkg_notes_formatted)) }}
        """
        data = data.replace("\n", p.toolkit.literal("<br>"))
        data = data.replace(p.toolkit.literal("</p><br>"), p.toolkit.literal("</p>"))

        return p.toolkit.literal("<p>") + p.toolkit.literal(data) + p.toolkit.literal("</p>")

    @staticmethod
    def hri_get_facet_items_dict(facet, limit=10, exclude_active=False):
        '''
        See ckan.lib.helpers.get_facet_items_dict for source, this is HACKed to fix broken scandic parameters.
        '''
        from ckan.common import request

        if not c.search_facets or \
                not c.search_facets.get(facet) or \
                not c.search_facets.get(facet).get('items'):
            return []
        facets = []
        for facet_item in c.search_facets.get(facet)['items']:

            if not len(facet_item['name'].strip()):
                continue

            # HACK Set broken facet item as 'active', if we are given the fixed one and its broken URL parameter is present.
            if facet == 'categories' and facet_item['name'] == u'Kaavat ja kiinteistöt' and ('categories', u'Kaavat ja kiinteist' + u"\ufffd" + u't') in request.params.items():
                facet_item['name'] = u'Kaavat ja kiinteist' + u"\ufffd" + 't'
                facets.append(dict(active=True, **facet_item))
                continue
            if facet == 'categories' and facet_item['name'] == u'Työ ja elinkeinot' and ('categories', u'Ty' + u"\ufffd" + u' ja elinkeinot') in request.params.items():
                facet_item['name'] = u'Ty' + u"\ufffd" + u' ja elinkeinot'
                facets.append(dict(active=True, **facet_item))
                continue
            if facet == 'categories' and facet_item['name'] == u'Väestö' and ('categories', u'V' + u"\ufffd" + u'est' + u"\ufffd") in request.params.items():
                facet_item['name'] = u'V' + u"\ufffd" + u'est' + u"\ufffd"
                facets.append(dict(active=True, **facet_item))
                continue
            if facet == 'categories' and facet_item['name'] == u'Ympäristö ja luonto' and ('categories', u'Ymp' + u"\ufffd" + u'rist' + u"\ufffd" + u' ja luonto') in request.params.items():
                facet_item['name'] = u'Ymp' + u"\ufffd" + u'rist' + u"\ufffd" + u' ja luonto'
                facets.append(dict(active=True, **facet_item))
                continue

            if not (facet, facet_item['name']) in request.params.items():
                facets.append(dict(active=False, **facet_item))
            elif not exclude_active:
                facets.append(dict(active=True, **facet_item))
        facets = sorted(facets, key=lambda item: item['count'], reverse=True)
        if c.search_facets_limits:
            limit = c.search_facets_limits.get(facet)
        if limit:
            return facets[:limit]
        else:
            return facets

    def get_helpers(self):
        # This method is defined in the ITemplateHelpers interface and
        # is used to return a dict of named helper functions.

        return {
            'wordpress_url': Hrifi.wordpress_url,
            'now': Hrifi.now,
            'make_facet_inputs': Hrifi.make_facet_inputs,
            'get_ga_code': Hrifi.get_ga_code,
            'solve_localized_value': Hrifi.solve_localized_value,
            'format_notes': Hrifi.format_notes,
            'hri_get_facet_items_dict': Hrifi.hri_get_facet_items_dict
        }


class WordPressAuthPlugin(p.SingletonPlugin):
    '''Reads WordPress login cookies to log user in.'''
    p.implements(p.IMiddleware, inherit=True)


    def make_middleware(self, app, config):
        return WordPressAuthMiddleware(app, config)
