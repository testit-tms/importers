"""Parsing and merge helpers for test run tags/links."""
import json
import logging
from typing import Any, Dict, List, Optional

_LINK_TYPES = frozenset({
    'Related',
    'BlockedBy',
    'Defect',
    'Issue',
    'Requirement',
    'Repository',
})


def parse_tags(raw: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated or JSON array tags. Empty/omitted -> None."""
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None

    if value.startswith('['):
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            logging.warning(f'Invalid test run tags JSON: {exc}')
            return None
        if not isinstance(data, list):
            logging.warning('Test run tags JSON must be an array of strings')
            return None
        tags = [str(item).strip() for item in data if str(item).strip()]
        return tags or None

    tags = [part.strip() for part in value.split(',') if part.strip()]
    return tags or None


def parse_links(raw: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    """Parse JSON array of link objects. Empty/omitted -> None."""
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None

    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        logging.warning(f'Invalid test run links JSON: {exc}')
        return None

    if not isinstance(data, list):
        logging.warning('Test run links JSON must be an array of objects')
        return None

    links: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            logging.warning(f'Skipping invalid test run link (not an object): {item}')
            continue
        url = item.get('url')
        if not url or not str(url).strip():
            logging.warning(f'Skipping test run link without url: {item}')
            continue

        link: Dict[str, Any] = {'url': str(url).strip()}
        if item.get('title') is not None:
            link['title'] = str(item['title'])
        if item.get('description') is not None:
            link['description'] = str(item['description'])

        link_type = item.get('type') or 'Related'
        link_type = str(link_type)
        if link_type.title() in _LINK_TYPES:
            link['type'] = link_type.title()
        elif link_type in _LINK_TYPES:
            link['type'] = link_type
        else:
            logging.warning(f'Unknown link type "{link_type}", using Related')
            link['type'] = 'Related'

        links.append(link)

    return links or None


def merge_tags(existing: Optional[List[str]], new: Optional[List[str]]) -> List[str]:
    merged: List[str] = []
    for tag in (existing or []) + (new or []):
        if tag and tag not in merged:
            merged.append(tag)
    return merged


def merge_links(
        existing: Optional[List[Dict[str, Any]]],
        new: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen_urls = set()

    for link in (existing or []) + (new or []):
        url = link.get('url')
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        merged.append(link)

    return merged
