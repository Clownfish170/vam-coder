"""Web glue."""


from text import slugify


def page_title(s):
    return slugify(s) + ".html"
