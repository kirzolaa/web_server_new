import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Union, Optional
from dataclasses import dataclass, asdict
import logging
import re
import random
from defines import getCreds, makeApiCall

# Configure logging
# logging.basicConfig(
#     level=logging.INFO, 
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler('instagram_fetcher.log', encoding='utf-8')
#     ]
# )
# logger = logging.getLogger(__name__)

@dataclass
class PostData:
    """Data class to store post information"""
    id: str
    caption: str
    timestamp: datetime
    likes: int
    comments: int
    media_type: str
    url: str
    location: Optional[str] = None
    hashtags: Optional[List[str]] = None

    def to_dict(self):
        """Convert PostData to dictionary"""
        return {
            k: str(v) if isinstance(v, datetime) else v 
            for k, v in asdict(self).items()
        }

class InstagramFetcher:
    """Instagram post fetcher using both Graph API and GraphQL API"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # Base delay in seconds
    RATE_LIMIT_DELAY = 30  # Delay when rate limited
    
    def __init__(self, use_graph_api: bool = False, 
                 max_posts: int = 10000000, 
                 login_username: Optional[str] = None, 
                 login_password: Optional[str] = None):
        """Initialize the fetcher
        
        Args:
            use_graph_api: If True, uses Graph API with credentials from defines.py.
                         If False, uses GraphQL API which works with any public username.
            max_posts: Maximum number of posts to fetch in a single operation
            login_username: Optional username for login (not used in current implementation)
            login_password: Optional password for login (not used in current implementation)
        """
        self.use_graph_api = use_graph_api
        self.max_posts = max_posts
        self.login_username = login_username
        self.login_password = login_password
        
        if use_graph_api:
            self.creds = getCreds()
            # logger.info("Instagram Graph API fetcher initialized")
        else:
            self.session = self._create_session()
            # logger.info("Instagram GraphQL API fetcher initialized")

    def _create_session(self) -> requests.Session:
        """Create a configured requests session with advanced anti-blocking techniques"""
        session = requests.Session()
        
        # Comprehensive, randomized headers to mimic real browser
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        
        user_agent = random.choice(user_agents)
        
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
        
        return session

    def _get_instagram_cookies(self, username: str) -> Dict[str, str]:
        """
        Simulate a full browser session to obtain necessary cookies with enhanced techniques
        
        Args:
            username: Instagram username to visit
        
        Returns:
            Dictionary of cookies
        """
        try:
            session = self._create_session()
            
            # Enhanced browser-like navigation
            headers = session.headers.copy()
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Visit Instagram homepage first with randomized delay
            homepage_url = 'https://www.instagram.com/'
            homepage_response = session.get(homepage_url, headers=headers)
            time.sleep(random.uniform(1.5, 3.5))
            
            # Visit user profile with additional headers
            profile_headers = headers.copy()
            profile_headers.update({
                'Referer': homepage_url,
                'Sec-Fetch-Site': 'same-origin'
            })
            profile_url = f'https://www.instagram.com/{username}/'
            profile_response = session.get(profile_url, headers=profile_headers)
            time.sleep(random.uniform(1.5, 3.5))
            
            # Extract and validate important cookies
            cookies = {
                'csrftoken': session.cookies.get('csrftoken', ''),
                'ig_did': session.cookies.get('ig_did', ''),
                'mid': session.cookies.get('mid', ''),
                'ig_nrcb': session.cookies.get('ig_nrcb', '1'),
                'ig_lang': session.cookies.get('ig_lang', 'en'),
                'datr': session.cookies.get('datr', '')
            }
            
            # Validate cookies
            if not all(cookies.values()):
                # logger.warning("Some cookies could not be retrieved")
                pass
            
            return cookies
        
        except Exception as e:
            # logger.error(f"Error obtaining Instagram cookies: {e}")
            pass
            return {}

    def _extract_hashtags(self, caption: str) -> List[str]:
        """Extract hashtags from caption"""
        return [word[1:] for word in (caption or '').split() if word.startswith('#')]

    def _handle_rate_limit(self, attempt: int):
        """Handle rate limiting with exponential backoff"""
        delay = self.RETRY_DELAY * (2 ** attempt) + random.uniform(0, 2)
        # logger.warning(f"Rate limited. Waiting {delay} seconds before retry.")
        time.sleep(delay)

    def _get_user_id(self, username: str) -> str:
        """Get user ID from username using GraphQL API with robust extraction"""
        try:
            url = f'https://www.instagram.com/{username}/'
            print(f"Attempting to fetch user ID for username: {username}")
            print(f"URL: {url}")
            
            headers = self.session.headers.copy()
            headers.update({
                'Referer': 'https://www.instagram.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            response = self.session.get(url, headers=headers)
            print(f"Response status code: {response.status_code}")
            response.raise_for_status()
            
            # Print the entire response text for debugging
            print("Response text (first 2000 characters):")
            print(response.text[:2000])
            
            # Multiple extraction methods for resilience
            extraction_methods = [
                r'"user_id":"(\d+)"',  # Most reliable method, moved to the top
                r'"id":"(\d+)"',
                r'window\._sharedData = ({.*?});',
                r'window\.__additionalDataLoaded\([^)]+,\s*({.*?})\);'
            ]
            
            for method in extraction_methods:
                match = re.search(method, response.text, re.DOTALL)
                if match:
                    try:
                        print(f"Matched method: {method}")
                        print(f"Match group: {match.group(1)}")
                        
                        if method == r'window\._sharedData = ({.*?});':
                            shared_data = json.loads(match.group(1))
                            user_data = shared_data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
                            if user_data and 'id' in user_data:
                                return user_data['id']
                        elif method == r'window\.__additionalDataLoaded\([^)]+,\s*({.*?})\);':
                            additional_data = json.loads(match.group(1))
                            user_data = additional_data.get('graphql', {}).get('user', {})
                            if user_data and 'id' in user_data:
                                return user_data['id']
                        else:
                            return match.group(1)
                    except Exception as parse_error:
                        print(f"Failed to parse user ID with method {method}: {parse_error}")
                        pass
            
            raise ValueError(f"Could not find user ID for {username}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error getting user ID for {username}: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error getting user ID for {username}: {str(e)}")
            raise

    def _get_user_posts_graphql(self, user_id: str, after: Optional[str] = None) -> List[PostData]:
        """
        Get user posts using GraphQL API with advanced anti-blocking techniques
        
        Args:
            user_id: Instagram user ID
            after: Pagination cursor
        
        Returns:
            List of PostData objects
        """
        try:
            # Prepare variables with randomized batch size
            batch_size = min(random.randint(500000, 10000000000), self.max_posts)
            variables = {
                'id': user_id,
                'first': batch_size,
                'after': after
            }
            
            print(f"Fetching posts for user ID: {user_id}")
            print(f"Batch size: {batch_size}")
            print(f"After cursor: {after}")
            
            # GraphQL endpoint
            url = 'https://www.instagram.com/graphql/query/'
            
            # Prepare query parameters
            params = {
                'query_hash': '472f257a40c653c64c666ce877d59d2b',  # Public posts query hash
                'variables': json.dumps(variables)
            }
            
            # Prepare headers
            headers = self.session.headers.copy()
            headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'X-IG-App-ID': '936619743392459',
                'Accept': '*/*',
                'Referer': f'https://www.instagram.com/p/{user_id}/',
            })
            
            # Maximum retry attempts
            for attempt in range(self.MAX_RETRIES):
                try:
                    print(f"Attempt {attempt + 1} to fetch posts")
                    
                    # Make the request
                    response = self.session.get(url, params=params, headers=headers)
                    
                    # Print response details
                    print(f"Response status code: {response.status_code}")
                    print(f"Response headers: {response.headers}")
                    
                    # Handle status codes
                    if response.status_code == 401:
                        print(f"Unauthorized access (Attempt {attempt + 1}). Rotating headers and session.")
                        # Regenerate entire session
                        self.session = self._create_session()
                        headers['User-Agent'] = random.choice([
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
                        ])
                        continue

                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + random.uniform(0, 5)
                        print(f"Rate limited. Waiting {wait_time} seconds.")
                        time.sleep(wait_time)
                        continue
                    
                    # Validate response
                    response.raise_for_status()
                    
                    # Try to parse JSON
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        print(f"Invalid JSON response: {response.text}")
                        break
                    
                    # Extract posts data
                    posts_data = data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {})
                    
                    # Explicitly print these lines for command output log
                    total_posts_count = posts_data.get('count', 'Unknown')
                    print(f"Total posts count: {total_posts_count}")
                    
                    # Process posts
                    posts: List[PostData] = []
                    edges = posts_data.get('edges', [])
                    
                    print(f"Number of post edges: {len(edges)}")
                    
                    for edge in edges:
                        try:
                            node = edge.get('node', {})
                            
                            # Extract caption
                            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                            caption = ''
                            try:
                                caption = caption_edges[0].get('node', {}).get('text', '')
                            except (IndexError, TypeError):
                                print(f"Could not extract caption for post {node.get('id', 'unknown')}")
                            
                            # Convert timestamp
                            timestamp = datetime.fromtimestamp(node.get('taken_at_timestamp', 0))
                            
                            # Create PostData object
                            post = PostData(
                                id=node.get('id', ''),
                                caption=caption,
                                timestamp=timestamp,
                                likes=node.get('edge_media_preview_like', {}).get('count', 0),
                                comments=node.get('edge_media_to_comment', {}).get('count', 0),
                                media_type=node.get('__typename', ''),
                                url=node.get('display_url', ''),
                                location=node.get('location', {}).get('name', None),
                                hashtags=self._extract_hashtags(caption)
                            )
                            
                            posts.append(post)
                        
                        except Exception as post_err:
                            print(f"Error processing individual post: {post_err}")
                    
                    # Check if there are more posts to fetch
                    page_info = posts_data.get('page_info', {})
                    has_next_page = page_info.get('has_next_page', False)
                    end_cursor = page_info.get('end_cursor')
                    
                    print(f"Successfully fetched {len(posts)} posts.")
                    print(f"Has next page: {has_next_page}")
                    
                    time.sleep(10)  # Respect rate limits
                    
                    # If there are more posts and we haven't reached max_posts, return posts and end_cursor
                    if has_next_page and end_cursor:
                        return posts, end_cursor
                    
                    return posts, None

                except (requests.exceptions.RequestException, json.JSONDecodeError) as req_err:
                    print(f"Request error on attempt {attempt + 1}: {req_err}")
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            
            return [], None
        
        except Exception as e:
            print(f"Unexpected error fetching posts: {str(e)}")
            raise

    def _get_user_posts_graph_api(self, user_id: str, after: Optional[str] = None) -> List[PostData]:
        """Get user posts using Graph API with enhanced error handling"""
        try:
            endpoint_params = {
                'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count',
                'access_token': self.creds['access_token'],
                'limit': min(100, self.max_posts)  # Limit batch size
            }
            if after:
                endpoint_params['after'] = after

            url = f"{self.creds['endpoint_base']}{self.creds['instagram_account_id']}/media"
            
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = makeApiCall(url, endpoint_params)
                    
                    if not response or 'json_data' not in response:
                        # logger.warning("Invalid API response")
                        return []
                    
                    data = response['json_data']
                    timeline = data.get('data', [])
                    
                    posts = []
                    for item in timeline[:self.max_posts]:
                        try:
                            timestamp = datetime.fromisoformat(item.get('timestamp', ''))
                            
                            post = PostData(
                                id=item.get('id', ''),
                                caption=item.get('caption', ''),
                                timestamp=timestamp,
                                likes=item.get('like_count', 0),
                                comments=item.get('comments_count', 0),
                                media_type=item.get('media_type', ''),
                                url=item.get('media_url', ''),
                                hashtags=self._extract_hashtags(item.get('caption', ''))
                            )
                            posts.append(post)
                        
                        except Exception as e:
                            # logger.warning(f"Error processing Graph API post: {str(e)}")
                            pass
                    
                    # logger.info(f"Successfully fetched {len(posts)} posts from Graph API")
                    return posts
                
                except Exception as api_err:
                    # logger.error(f"Error in Graph API post fetching (attempt {attempt + 1}): {api_err}")
                    if attempt == self.MAX_RETRIES - 1:
                        raise
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            
            return []
        
        except Exception as e:
            # logger.error(f"Unexpected error in Graph API fetching: {str(e)}")
            pass
            raise

    def fetch_user_posts(self, username: Optional[str] = None, method: str = "recent", 
                    count: Optional[int] = None, since_date: Optional[datetime] = None, 
                    until_date: Optional[datetime] = None) -> List[PostData]:
        """
        Fetch posts using different methods with enhanced flexibility and error handling
        
        Args:
            username: Username to fetch posts from (required if use_graph_api=False)
            method: One of ["recent", "all", "top", "date_range"]
            count: Number of posts to fetch (for recent/top methods)
            since_date: Start date for date_range method
            until_date: End date for date_range method
        """
        try:
            if not self.use_graph_api and not username:
                raise ValueError("Username is required when not using Graph API")
            
            posts = []
            after = None
            
            # Determine the method for fetching posts
            if self.use_graph_api:
                while len(posts) < (count or self.max_posts):
                    try:
                        data = self._get_user_posts_graph_api(after)
                        
                        if not data:
                            break
                        
                        filtered_posts = self._filter_posts(data, method, since_date, until_date)
                        posts.extend(filtered_posts)
                        
                        # Break if we've reached the desired count or no more posts
                        if count and len(posts) >= count:
                            posts = posts[:count]
                            break
                        
                        # Update pagination token (this might need adjustment based on Graph API response)
                        after = data[-1].id if data else None
                        
                        if not after:
                            break
                    
                    except Exception as api_err:
                        # logger.error(f"Error in Graph API post fetching: {api_err}")
                        pass
                        break
            
            else:
                # GraphQL method
                user_id = self._get_user_id(username)
                
                while len(posts) < (count or self.max_posts):
                    try:
                        # New method returns (posts, next_cursor)
                        data, next_cursor = self._get_user_posts_graphql(user_id, after)
                        
                        if not data:
                            break
                        
                        filtered_posts = self._filter_posts(data, method, since_date, until_date)
                        posts.extend(filtered_posts)
                        
                        # Break if we've reached the desired count or no more posts
                        if count and len(posts) >= count:
                            posts = posts[:count]
                            break
                        
                        # Update pagination token
                        after = next_cursor
                        
                        if not after:
                            break
                    
                    except Exception as graphql_err:
                        # logger.error(f"Error in GraphQL post fetching: {graphql_err}")
                        pass
                        break
            
            return posts
        
        except Exception as e:
            # logger.error(f"Unexpected error in post fetching: {str(e)}")
            pass
            raise

    def _filter_posts(self, posts: List[PostData], method: str, 
                      since_date: Optional[datetime] = None, 
                      until_date: Optional[datetime] = None) -> List[PostData]:
        """
        Filter posts based on method and date range
        
        Args:
            posts: List of posts to filter
            method: Filtering method
            since_date: Start date for filtering
            until_date: End date for filtering
        
        Returns:
            Filtered list of posts
        """
        filtered_posts = []
        
        for post in posts:
            # Date range filtering
            if since_date and post.timestamp < since_date:
                continue
            if until_date and post.timestamp > until_date:
                continue
            
            # Method-based filtering
            if method == "top":
                # You might want to define a custom scoring mechanism for "top" posts
                if post.likes + post.comments > 100:  # Example threshold
                    filtered_posts.append(post)
            else:
                filtered_posts.append(post)
        
        return filtered_posts

    def save_to_excel(self, posts: List[PostData], filepath: str):
        """
        Save posts to Excel file with enhanced data handling
        
        Args:
            posts: List of PostData objects
            filepath: Path to save the Excel file
        """
        try:
            # Convert posts to a list of dictionaries for DataFrame
            posts_dict = [post.to_dict() for post in posts]
            
            df = pd.DataFrame(posts_dict)
            
            # Ensure datetime columns are formatted correctly
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Save to Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            # logger.info(f"Successfully saved {len(posts)} posts to {filepath}")
        
        except Exception as e:
            # logger.error(f"Error saving posts to Excel: {str(e)}")
            pass
            raise

def main():
    """Example usage"""
    try:
        # Get username from user input
        username = input("Enter Instagram username to fetch posts from (or press Enter to use Graph API): ").strip()
        
        # Initialize fetcher based on whether username was provided
        use_graph_api = not username
        fetcher = InstagramFetcher(use_graph_api=use_graph_api)
        
        # logger.info("Starting to fetch all posts...")
        
        # Fetch all posts
        posts = fetcher.fetch_user_posts(
            username=username if not use_graph_api else None,
            method="all"  # This will fetch all posts without limit
        )
        
        # logger.info(f"Successfully fetched {len(posts)} posts")
        
        # Save to Excel with timestamp and username in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"instagram_posts_{username if username else 'graph_api'}_{timestamp}.xlsx"
        fetcher.save_to_excel(posts, filename)
        
        # logger.info(f"All posts have been saved to {filename}")
        
    except Exception as e:
        # logger.error(f"Error in main: {str(e)}")
        pass

if __name__ == "__main__":
    main()
