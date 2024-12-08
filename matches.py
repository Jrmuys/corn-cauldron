import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# List of Steam Account IDs to track
STEAM_ACCOUNT_IDS = [81030588, 129300751, 104889569, 104458277, 119734677, 128463449]

# Get API endpoint and key from environment variables
API_ENDPOINT = os.getenv('DOTA_API_ENDPOINT')
API_KEY = os.getenv('DOTA_API_KEY')

# Check if API credentials are set
if not API_ENDPOINT or not API_KEY:
    raise ValueError("Please set DOTA_API_ENDPOINT and DOTA_API_KEY in your .env file")

def get_latest_match_ids():
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
        'User-Agent': 'STRATZ_API'
    }
 
    for i in range(0, len(STEAM_ACCOUNT_IDS), 5):
        # Take a slice of 5 IDs (or fewer for the last batch)
        current_batch = STEAM_ACCOUNT_IDS[i:i+5]
        
        # Convert Steam Account IDs to string for the query
        ids_string = ','.join(map(str, current_batch))
        
        # GraphQL query
        query = '''
        {
          players(steamAccountIds:[%s]) {
            matches(request:{
              isParty: true,
              limit: 1
            }) {
              id
            }
          }
        }
        ''' % ids_string
        
        # Prepare payload
        payload = {
            'query': query
        }
        
        try:
            # Make the API request
            response = requests.post(API_ENDPOINT, json=payload, headers=headers)
            
            # Raise an exception for bad responses
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Process matches for this batch
            match_ids = [
                match.get('id')
                for player in data.get('data', {}).get('players', [])
                for match in player.get('matches', [])
            ]
            
            # Return the list of match IDs
            return match_ids
        
        except requests.RequestException as e:
            print(f"Error fetching match IDs for batch {current_batch}: {e}")
 
                

def fetch_dota_matches():
    # Calculate the timestamp for 24 hours ago
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=2)
    
    # Convert to Unix timestamp (seconds since epoch)
    end_timestamp = int(end_time.timestamp())
    start_timestamp = int(start_time.timestamp())

    # Process matches in batches of 5 Steam IDs
    all_processed_matches = []
    processed_match_ids = set()
    items = set()

    # Split Steam Account IDs into batches of 5
    for i in range(0, len(STEAM_ACCOUNT_IDS), 5):
        # Take a slice of 5 IDs (or fewer for the last batch)
        current_batch = STEAM_ACCOUNT_IDS[i:i+5]
        
        # Convert Steam Account IDs to string for the query
        ids_string = ','.join(map(str, current_batch))

        # GraphQL query
        query = '''
        {
          players(steamAccountIds:[%s]) {
            matches(request:{
              isParty: true,
              endDateTime: %d,
              startDateTime: %d
            }) {
              midLaneOutcome,
              radiantKills,
              direKills,
              radiantNetworthLeads,
              radiantExperienceLeads,
              durationSeconds,
              bottomLaneOutcome,
              topLaneOutcome,
              averageRank,
              actualRank,
              rank,
              id,
              startDateTime,
              didRadiantWin,
              players {
                steamAccount {
                  id,
                  name,
                  avatar,
                  smurfFlag
                }
                role,
                item0Id,
                item1Id,
                item2Id,
                item3Id,
                item4Id,
                item5Id,
                award,
                neutral0Id,
                isRadiant,
                kills,
                lane,
                deaths,
                assists,
                networth
                hero {
                  shortName,
                  name,
                  id,
                }
              }  
            }
          }
        }
        ''' % (ids_string, end_timestamp, start_timestamp)

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}',
            'User-Agent': 'STRATZ_API'

        }

        # Prepare payload
        payload = {
            'query': query
        }

        try:
            # Make the API request
            response = requests.post(API_ENDPOINT, json=payload, headers=headers)
            
            # Raise an exception for bad responses
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Process matches for this batch
            batch_matches = process_matches(data, processed_match_ids)
            
            # Add new unique matches to the overall list
            all_processed_matches.extend(batch_matches)
            for match in batch_matches:
                for player in match['players']:
                    for item in player['items']:
                        items.add(item)
        
        except requests.RequestException as e:
            print(f"Error fetching matches for batch {current_batch}: {e}")



    return all_processed_matches

def get_items():
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
        'User-Agent': 'STRATZ_API'
    }
    
    # Prepare payload
    payload = {
        'query': '''
        {
            constants{
                items {
                    id,
                    name,
                    image
                }
            }
        }
        '''
    }
    
    try:
        # Make the API request
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        
        # Raise an exception for bad responses
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # Return the list of items
        return data.get('data', {}).get('items', [])
    
    except requests.RequestException as e:
        print(f"Error fetching items: {e}")
        return []
    

def process_matches(response_data, processed_match_ids):
    # List to store processed matches for this batch
    processed_matches = []
    
    # Navigate through the response structure
    players = response_data.get('data', {}).get('players', [])
    
    # Iterate through each player's matches
    for player in players:
        matches = player.get('matches', [])
        
        for match in matches:
            match_id = match.get('id')
            
            # Skip if we've already processed this match
            if match_id in processed_match_ids:
                continue
            
            # Get the Steam Account IDs in this match
            match_account_ids = set(
                player_detail.get('steamAccount', {}).get('id')
                for player_detail in match.get('players', [])
            )
            
            # Check if at least two of our tracked accounts are in this match
            matching_accounts = match_account_ids.intersection(STEAM_ACCOUNT_IDS)
            if len(matching_accounts) < 2:
                continue
            
            # Mark this match as processed
            processed_match_ids.add(match_id)
            
            match_info = {
                'match_id': match_id,
                'start_datetime': match.get('startDateTime'),
                'radiant_win': match.get('didRadiantWin'),
                'duration_seconds': match.get('durationSeconds'),
                'average_rank': match.get('averageRank'),
                'radiant_kills': match.get('radiantKills'),
                'dire_kills': match.get('direKills'),
                'lane_outcomes': {
                    'mid': match.get('midLaneOutcome'),
                    'bottom': match.get('bottomLaneOutcome'),
                    'top': match.get('topLaneOutcome')
                },
                'matched_account_ids': list(matching_accounts),
                'players': []
            }
            
            # Process player details for this match
            for player_detail in match.get('players', []):
                player_info = {
                    'steam_account_id': player_detail.get('steamAccount', {}).get('id'),
                    'steam_account_name': player_detail.get('steamAccount', {}).get('name'),
                    'is_radiant': player_detail.get('isRadiant'),
                    'hero': {
                        'id': player_detail.get('hero', {}).get('id'),
                        'short_name': player_detail.get('hero', {}).get('shortName'),
                        'name': player_detail.get('hero', {}).get('name')
                    },
                    'performance': {
                        'kills': player_detail.get('kills'),
                        'deaths': player_detail.get('deaths'),
                        'assists': player_detail.get('assists'),
                        'networth': player_detail.get('networth'),
                        'lane': player_detail.get('lane'),
                        'role': player_detail.get('role')
                    },
                    'items': [
                        player_detail.get(f'item{i}Id') for i in range(6)
                    ],
                    'neutral_item': player_detail.get('neutral0Id')
                }
                
                match_info['players'].append(player_info)
            
            processed_matches.append(match_info)
    
    return processed_matches


# Example usage
def main():
    print("Getting matches...")
    matches = fetch_dota_matches()
    
    if matches:
        print(f"Total unique matches found: {len(matches)}")
        
        # Print or further process the matches
        for match in matches:
            # Convert timestamp to readable datetime
            match_time = datetime.fromtimestamp(match['start_datetime'])
            
            print(f"Match ID: {match['match_id']}")
            print(f"Match Time: {match_time}")
            print(f"Radiant Win: {match['radiant_win']}")
            print(f"Matched Account IDs: {match['matched_account_ids']}")
            print("Players:")
            for player in match['players']:
                print(f"  - {player['steam_account_name']} ({player['hero']['short_name']})")
                if (player['steam_account_name'] == 'Jerboa'):
                    print(player)
            print("\n")
            
            
        

if __name__ == '__main__':
    main()