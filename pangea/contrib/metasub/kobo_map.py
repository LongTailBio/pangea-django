import requests


def refresh_kobo_user(kobo_user):
    try:
        kobo_user.refresh_token()
    except:
        print('Failed to get token for Kobo User', file=sys.stderr)
        raise
    try:
        kobo_user.get_assets()
    except:
        print('Failed to get assets for Kobo User', file=sys.stderr)
        raise       
    for asset in kobo_user.kobo_assets.all():
        refresh_kobo_asset(asset)


def refresh_kobo_asset(asset):
    try:
        asset.get_results()
    except:
        print('Failed to get results for Kobo Asset', file=sys.stderr)
        raise   