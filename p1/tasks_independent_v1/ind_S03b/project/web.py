"""Web glue."""


from util import slugify


def page_title(s):
    return slugify(s) + ".html"
