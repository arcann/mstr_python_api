import functools


class MemoizeClass(type):
    """
    Memoize parent class to preserve memory.

    Objects are considered to be the same, and thus a new object
    does not need to be instantiated, if an object with given parameters already exists.
    """

    @functools.lru_cache(maxsize=5000)
    def __call__(cls, *args, **kwargs):
        """
        Called when a new Singleton object is created.

        Singleton class checks to see if there is already a copy
        of the object in the class instances, and if so returns
        that object. Otherwise, it creates a new object of that
        subclass type.
        """
        return super(MemoizeClass, cls).__call__(*args, **kwargs)
