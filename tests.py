import requests

def test_api():
    response = requests.get('http://localhost:8000/mill-config/?type=Carding')
    
    # Print status and response content
    print('Status Code:', response.status_code)
    print('Response Content:', response.text)  # This will show what the server is returning

    if response.ok:
        try:
            data = response.json()
            print('Response for Carding:', data)
        except ValueError:
            print('Response content is not valid JSON.')
    else:
        print('Failed to retrieve data.')

# Run the test
test_api()
