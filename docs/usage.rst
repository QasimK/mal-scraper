==============
Usage/Examples
==============

To use MyAnimeList Scraper in a project, for example to retrieve
anime metadata::

    import mal_scraper
    import mycode

    next_id_ref = mycode.last_id_ref() + 1

    try:
        meta, data = mal_scraper.get_anime(next_id_ref)
    except requests.exceptions.HTTPError as err:
        code = err.response.status_code
        if code == 404:
            print('Anime #%d does not exist (404)', next_id_ref)
            mycode.ignore_id_ref(next_id_ref)
        else:
            # Retry on network/server/request errors
            print('Anime #%d HTTP error (%d)', next_id_ref, code)
            mycode.mark_for_retry(next_id_ref)
    else:
        print('Adding Anime #%d', meta['id_ref'])
        mycode.add_anime(
            id_ref=meta['id_ref'],
            anime_information_dated_at=meta['when'],
            name=data['name'],
            episodes=data['episodes'],
            # Ignore other data
        )
