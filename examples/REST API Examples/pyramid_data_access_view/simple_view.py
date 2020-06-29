"""
Simple view decorator. Puts the view path directly into the method decorator instead of having to link by route name.

Created on Oct 5, 2015

@source: http://madjar.github.io/europython2013
"""
import inspect
import logging

import venusian
from pyramid.request import Request

log = logging.getLogger(__name__)


def _combine_route_name_parts(root_base: str, route_suffix: str) -> str:
    if route_suffix is not None:
        return root_base + '_' + route_suffix
    else:
        return root_base


def simple_route_path(request: Request, root_base: str, route_suffix: str = None, **kwargs):
    route_name = _combine_route_name_parts(root_base, route_suffix)
    return request.route_path(route_name, **kwargs)


def _add_simple_view(config,
                     view,
                     path,
                     route_suffix=None,
                     root_factory=None,
                     renderer=None,
                     permission=None,
                     title=None,
                     index_category=None,
                     example_args=None):
    route_name = _combine_route_name_parts(view.__name__, route_suffix)
    log.debug('_add_simple_view: view %s path %s route_name %s renderer %s permission %s',
              view, path, route_name, renderer, permission)
    log.debug('_add_simple_view: view file %s', inspect.getfile(view))

    config.add_route(route_name, path, factory=root_factory)
    config.add_view(view,
                    route_name=route_name,
                    renderer=renderer,
                    permission=permission)
    if title is not None:
        config.add_index_entry(title=title,
                               route_name=route_name,
                               path=path,
                               index_category=index_category,
                               example_args=example_args
                               )


def add_simple_view(config,
                    view,
                    path,
                    route_suffix=None,
                    renderer=None,
                    permission=None,
                    title=None,
                    index_category=None,
                    example_args=None):
    """
    Adds a directive `add_simple_view` to pyramid config.
    
    Registered with:
    config.add_directive('add_simple_view', add_simple_view)
    
    http://madjar.github.io/europython2013/#/step-26
    """

    def callback():
        _add_simple_view(config=config,
                         view=view,
                         path=path,
                         route_suffix=route_suffix,
                         renderer=renderer,
                         permission=permission,
                         title=title,
                         index_category=index_category,
                         example_args=example_args
                         )

    # The discriminator uniquely identifies the action.
    # It must be given, but it can be None, to indicate that the action never conflicts. It must be a hashable value.
    discriminator = ('add_simple_view', path)
    # Register an action which will be executed when pyramid.config.Configurator.commit()
    config.action(discriminator, callback)


class SimpleView(object):
    """
    Simple view decorator. 
    
    Usable as:
    
        @simple_view('/')
        def view(request):
            return Response('It is I, Arthur, son of Uther Pendragon, ...')
    
    http://madjar.github.io/europython2013/#/step-27
    """

    def __init__(self,
                 path,
                 route_suffix=None,
                 renderer=None,
                 permission=None,
                 title=None,
                 index_category=None,
                 example_args=None,
                 root_factory=None,
                 ):
        self.path = path
        self.route_suffix = route_suffix
        self.root_factory = root_factory
        self.renderer = renderer
        self.permission = permission
        self.title = title
        self.index_category = index_category
        self.example_args = example_args

    def __call__(self, wrapped):
        # log.debug('wrapped{}'.format(wrapped))
        settings = self.__dict__.copy()

        # pylint: disable=unused-argument
        # noinspection PyUnusedLocal
        def register(context, name, view):
            config = context.config.with_package(info.module)
            # log.debug('simple_view: context {} name {} view {} path {}'.format(context, name, view, self.path))

            _add_simple_view(config=config,
                             view=view,
                             route_suffix=self.route_suffix,
                             root_factory=self.root_factory,
                             path=self.path,
                             renderer=self.renderer,
                             permission=self.permission,
                             title=self.title,
                             index_category=self.index_category,
                             example_args=self.example_args,
                             )

        # Attach the callback function above
        # venusian decorators, are detected by config.scan()
        info = venusian.attach(wrapped,
                               register,
                               category='pyramid',
                               )

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        # Copied from view_config decorator
        settings['_info'] = info.codeinfo  # fbo "action_method"
        return wrapped
