# WildApricot API
Example Code taken from wildapricot github, and modified to work for me.

[Wild Apricot Samples](https://github.com/WildApricot/ApiSamples)

## Example Usage:
```python
def getContactById(id):
    # Create API and authenticate by api key
    api = WaApiClient(api_key=os.environ['WA_API_KEY'])
    api.authenticate_with_apikey()
    # Get all accounts
    account = self.api.execute_request("/v2/accounts")[0]

    # Get Contacts URL from API Response
    contactsUrl = next(res for res in account['Resources'] if res['Name'] == 'Contacts')['Url']

    # Request Client Info
    params = {'$async': 'false'}
    request_url = contactsUrl + str(id) +  '?' + urllib.parse.urlencode(params)
    response = api.execute_request(request_url)
    print(response)
```