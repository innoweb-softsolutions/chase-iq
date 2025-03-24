"""
Selenium-based Facebook scraping components
"""
from .browser import BrowserManager
from .auth import FacebookAuthenticator
from .scrapers import GroupScraper, PageScraper
from .extractors import PostExtractor

__all__ = [
    'BrowserManager',
    'FacebookAuthenticator',
    'GroupScraper',
    'PageScraper',
    'PostExtractor'
]