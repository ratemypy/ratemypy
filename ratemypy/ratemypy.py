"""An unofficial Python API for Rate My Professors."""

import json
import random
import requests
import string
from typing import List, Union
import useragents



class Professor:
    """A professor in the RMP database."""
    def __init__(self, result):
        # Check to make sure we're receiving the correct type of result
        if result['content_type_s'] != 'TEACHER':
            raise ValueError(f"Expected 'content_type_s' to be 'TEACHER', instead got '{result['content_type_s']}'")

        # Name
        self.name = self.check_key('teacherfullname_s', result)
        self.firstname = self.check_key('teacherfirstname_t', result)
        self.lastname = self.check_key('teacherlastname_t', result)

        # Ratings
        self.overall = self.check_key('averageratingscore_rf', result)
        self.difficulty = self.check_key('averageeasyscore_rf', result)
        # self.takeagain = ???  # This is missing from the JSON...

        # Other ratings that don't show up in the UI
        # self.clarity = self.check_key('averageclarityscore_rf', result)
        # self.helpful = self.check_key('averagehelpfulscore_rf', result)
        # self.hotness = self.check_key('averagehotscore_rf', result)  # Deprecated, gives garbage numbers

        # Other Information
        self.department = self.check_key('teacherdepartment_s', result)

        # Metadata
        self.id = self.check_key('pk_id', result)  # Can be used to get the professor's URL
        self.annotated_id = self.check_key('id', result)  # This is `teacher:` followed by self.id
        
        self.pageviews = self.check_key('pageviews_i', result)
        self.last_rated = self.check_key('rated_date_dt', result)  # In YYYY-MM-DDTHH:MM:SSZ format
        self.url = f'https://www.ratemyprofessors.com/ShowRatings.jsp?tid={self.id}'

        # Unrecognized values
        # self.visible = result['visible_i']  # Usually `1`
        # self.timestamp = result['timestamp']  # Same format as `last_rated`, doesn't seem to correspond to anything
        # self.status = result['status_i']  # Usually `1`


    def __repr__(self):
        return f'<Professor [{self.name}]>'
    
    
    @staticmethod
    def check_key(key: str, result: dict) -> Union[str, None]:
        """Check if the given key is in the mapping given by `result` and return it if so."""
        try:
            return result[key]
        except KeyError:
            return None


# class University:
#         "city_state_s": "Waterloo_ON"
#         "schoolcity_s": "Waterloo"
#         "schoolstate_full_s": "Ontario"
#         "schoolcountry_s": "Canada"
#         "schoolname_s": "Wilfrid Laurier University-Waterloo"
#         "schoolstate_s": "ON"
#         "schoolid_s": "1492"
#         "schoolwebpage_s": "http://www.wlu.ca"


# class Rating:
#     "total_number_of_ratings_i": 16



def search(query: str, find: str = 'professors', limit: int = 20) -> Union[List[Professor]]:#, List[University]]:
    """Return a list of professors or universities matching the search term.
    
    - `query` can be any string
    - `find` can be either '`professors`' or '`universities`'
    - The website defaults to `20` for the limit -- set it higher at your own risk
    """
    def generate_random_referer() -> str:
        """Generate a random `referer` header to keep the requests looking organic."""
        base = 'https://www.ratemyprofessors.com/search.jsp?query='
        random_query = ''.join(random.choices(string.ascii_lowercase + ' ', k=random.randint(3, 12)))

        return base + random_query
    

    def get_items(items: dict, item_type: str = find) -> Union[list, None]:
        """Extract professors or universities from the given JSON response."""
        groups = items['grouped']['content_type_s']['groups']

        if not groups:  # If no results were returned
            return None
        
        if item_type == 'professors' and groups[0]['groupValue'] == 'TEACHER':
            return groups[0]['doclist']['docs']
        
        if item_type == 'universities':
            if groups[0]['groupValue'] == 'SCHOOL':
                return groups[0]['doclist']['docs']
            
            if len(groups) > 1 and groups[1]['groupValue'] == 'SCHOOL':
                return groups[1]['doclist']['docs']


    url = 'https://solr-aws-elb-production.ratemyprofessors.com//solr/rmp/select/'
    params = {  # Leaving lots of these settings alone to avoid raising any flags
        'solrformat': 'true',
        'rows': limit,
        'wt': 'json',
        'json': 'wrf:noCB',
        'callback': 'noCB',
        'q': query,
        'defType': 'edismax',
        'qf': 'teacherfirstname_t^2000 teacherlastname_t^2000 teacherfullname_t^2000 autosuggest',
        'bf': 'pow(total_number_of_ratings_i,1.7)',
        'sort': 'score desc',
        'siteName': 'rmp',
        'group': 'on',
        'group.field': 'content_type_s',
        'group.limit': limit
    }
    headers = {  # Make the request look more genuine
        'dnt': '1',
        'referer': generate_random_referer(),
        'user-agent': useragents.random_ua()
    }

    res = requests.get(url, params=params, headers=headers)
    items = get_items(json.loads(res.text))

    if find == 'professors':
        return [Professor(item) for item in items]
    
    # if find == 'universities':
    #     return [University(item) for item in items]
    
    raise ValueError(f"Unexpected value '{find}' for argument 'find' -- expected 'professors' or 'universities'")


if __name__ == '__main__':
    search_results = search('Ken')
    print(search_results)
    print()
