# import module
import requests
import os.path as path
import time
import datetime as dt
from dateutil.relativedelta import relativedelta
import warnings as wn

wn.filterwarnings('ignore')
print("""WARNING: No HTTPS Certificate Verification Enabled. Use of this program
         to access the SEPA hydrology data API may expose the user to security 
         risks including but not limited to MITM attacks, Phishing and Confidential 
         Data theft. This program should be used at your own risk. If you do not
         wish to continue using this program please close the program
         """)

print("""Note 1:  This program aims to provide easy access to a useful range of the
         data available from the SEPA hydrology data API. The full API provides 
         considerable more functionality and more info can be found here:
             
         https://timeseriesdoc.sepa.org.uk/
         
         It is important that you understand the types of data availiable and what 
         its limitations are. All data obtained using this program should be checked
         to confirm its validity. Though efforts have been made to avoid incorect 
         data being returned there is no guarantee of the currentness or correctness
         of any data returned and by using this program. The user accepts that they 
         are competent and have reviewed the code used in this program (availiable as 
         a *.py file alongside this *.exe) to ensure it meets thir requirements and 
         will review all data obtained using this program, to ensure it is correct
         and sutiable for the purpose for which they intend it for.
         """)

print("""Note 2:  Access to the SEPA hydrology data API can be Registered (5000 
         credits per day), or Un-Registered (500 credits per day). If you wish to 
         use an access key please obtain an API access key and save it as a text 
         file called 'accessKey.txt' in the same folder as this programs executable.
         API access keys can be obtained as discussed in:
         
         https://timeseriesdoc.sepa.org.uk/api-documentation/before-you-start/what-controls-there-are-on-access/
         
         If you have an access key set up select 'Y' below. Otherwise please select
         'N' for more limited unregistered access""")
         
def ObtainAccessToken(accessKey):
    """
    Used to obtain a current valid access token. The age of the 'accessToken.txt' log file
    is checked and if it was last modified less than 23 hours ago the access token is read
    from the file. If the age of 'accessToken.txt' is greater than 23 hours then a new 
    access token is requested using the API access key provided by SEPA.
    """
    
    if time.time() - path.getmtime(r'authentication\accessToken.txt') > 82800:
        
        print('Access Token Expired: Requesting New Token...')
        
        # specify target, key, header
        tokenURL = 'https://timeseries.sepa.org.uk/KiWebPortal/rest/auth/oidcServer/token'
        authHeaders = { 'Authorization' : 'Basic ' + accessKey }
        
        # POST token request to return response object 
        responseToken= requests.post(tokenURL, headers = authHeaders, data = 'grant_type=client_credentials', verify=False)
        
        # retrieve access token from response object
        accessToken = responseToken.json()['access_token']
        
        with open(r'authentication\accessToken.txt', 'w') as file:
            file.write(accessToken)
            
    if time.time() - path.getmtime(r'authentication\accessToken.txt') <= 82800:
        
        print('Access Token Current: Reading Token From File...')
        
        with open(r'authentication\accessToken.txt', 'r') as file:
            accessToken = file.read()

    return accessToken


def API_url_request(requestURL, accessKey, return_type='list', use_key='y'):
    """
    Adds a csv format request to the request url. Generates the header dictionary with a current 
    access token either from file (if current) or by requesting a new token using the API key. 
    Requests the response data from the request url in csv (comma seperated value format).
    There is then two options which are selected by setting 'return_type' to either 'list' or 'str'.
    Setting it to 'list' is used when the response is not a final output and is to make it easily
    searchable where as 'str' is used when the output is to be written to a .csv file. 
    """
    
    requestURL += '&format=csv&csvdiv=,' 
    print('\nRequest URL >>', requestURL, '\n')
    if use_key == 'y':
        
        accessToken = ObtainAccessToken(accessKey)
        headDict = {'Authorization':'Bearer ' + accessToken}
    
        if return_type == 'list':
            resp = [i.split(',') for i in requests.get(requestURL, headers = headDict, verify=False).text.split('\n')]
            if 'Credit limit exceeded' in resp[0][0]:
                raise ValueError('Error: Credit Limit Exceeded! Please try again in 24H, try using the unregistered option or use a different API Key.')
        
        if return_type == 'str':
            resp = requests.get(requestURL, headers = headDict, verify=False).text.split('\n')
            if 'Credit limit exceeded' in resp[0]:
                raise ValueError('Error: Credit Limit Exceeded! Please try again in 24H, try using the unregistered option or use a different API Key.')
    
    elif use_key == 'n':
        if return_type == 'list':
            resp = [i.split(',') for i in requests.get(requestURL, verify=False).text.split('\n')]
            if 'Credit limit exceeded' in resp[0][0]:
                raise ValueError('Error: Credit Limit Exceeded! Please try again in 24H, try using the unregistered option or use a different API Key.')
        
        if return_type == 'str':
            resp = requests.get(requestURL, verify=False).text.split('\n')
            if 'Credit limit exceeded' in resp[0]:
                raise ValueError('Error: Credit Limit Exceeded! Please try again in 24H, try using the unregistered option or use a different API Key.')
    
    return resp

def WriteCSV(responseData, output_folder='.', output_name='temp_output'):
    with open(output_folder + '\\' + output_name + '.csv', 'w') as file:
        file.write(responseData)
    return


def filter_by_type():
    ids = ['0', '1', '2', '3', '4', '5']
    types = ['all', 'RE,RS', 'SG', 'Q', 'GWL', 'TL']
    descriptions = ['No Station Type Filter', 'Rainfall (mm)', 'River Level (m)', 'River Flow (m3/s)', 'Groundwater Level (m)', 'Tidal Level (m)']
    
    print('Filter By Station Type\n')
    for i in range(6): print(ids[i], descriptions[i])
    
    selection = None
    while selection not in ids:
        if selection == None:
            selection = input('\nSelect row by typing the row number here >> ')
        else:
            print('\nRow value selected was outwith acceptable range of integers [0 - 5]. Please Try again.')
            selection = input('\nSelect row by typing the row number here >> ')

    selection = int(selection)
        
    if selection > 0:
        print('\nStation Type Selected ==', descriptions[selection])
        return '&stationparameter_no=' + types[selection]  
    if selection == 0:
        print('\nNo station type filter applied.')
        return ''
        
def filter_by_name():
    print('\nFilter By Station Name\n')
    print("""There are various ways to filter by station name. These include:
    - First Letter (e.g. type: B)
    - First Few Letters (e.g. type: Bal)
          
If you do not want to search by name please press ENTER""")

    search_term = input('\nType your search text here as per the examples above >> ')
    
    if search_term == '':
        print('\nNo station name filter applied.\n')
        return ''
    
    else:
        print('\nStation Name Filter Applied ==', search_term)
        return '&station_name=' + search_term + '*'
    
    
def CreateURL():
    baseURL = 'https://timeseries.sepa.org.uk/KiWIS/KiWIS?data-source=0&request=getStationList'
    type_filter = filter_by_type()    
    name_filter = filter_by_name()
    
    returnfields = '&returnfields=station_name,station_no,station_id,stationparameter_name,station_carteasting,station_cartnorthing'
    
    return baseURL + type_filter + name_filter + returnfields + '&object_type=General'


def RowSelect(responseData, columns):
    str_lengths = []
    for column in range(columns):
        temp = []
        for row in responseData:
            temp.append(len(row[column])+2)
        str_lengths.append(max(temp))
    
    ids = []
    for count, value in enumerate(responseData):
        print(str(count).ljust(4),end='')
        for i in range(columns):
            print(value[i].ljust(str_lengths[i]), end='')
        
        print('')
        
        ids.append(str(count))
    
    selection = None
    while selection not in ids:
        if selection == None:
            selection = input('\nSelect row by typing the row number here >> ')
        else:
            print('\nRow value selected was outwith acceptable range of integers [0 - ' + ids[-1] + ']. Please Try again.')
            selection = input('\nSelect row by typing the row number here >> ')
    
    selection = int(selection)
        
    if selection > 0:
        row = responseData[selection]
        print('\nSelection >>', str(selection).ljust(3), str(row))
    if selection == 0:
        raise ValueError('\nNo Row selected. Terminating Program. Please Start Again.')

    return row


def SelectStation(accessKey, use_key):   
        
    #Filter Stations
    requestURL = CreateURL()

    responseData = API_url_request(requestURL, accessKey, return_type='list', use_key=use_key)
        
    responseData[0] = ['Station Name', 'Station No.', 'Station ID', 'Station Type', 'Station Easting', 'Station Northing']
    
    row = RowSelect(responseData, 6)
    
    station_details = row
    
    #Select Timeseries Data Type
    base_url = 'https://timeseries.sepa.org.uk/KiWIS/KiWIS?service=kisters&type=queryServices&datasource=0&request=getTimeseriesList'
    return_fields = ','.join(['site_no', 'station_no', 'stationparameter_no', 'ts_shortname', 'ts_id', 'coverage'])
    
    requestURL = '&'.join([base_url, 'station_no=' + row[1], 'stationparameter_name=' + row[3], 'returnfields=' + return_fields])
    
    responseData = API_url_request(requestURL, accessKey, return_type='list', use_key=use_key)
           
    row = RowSelect(responseData, 7)  
    
    station_details.extend(row[2:4])
    
    #Generate Final Output CSV
    base_url = 'https://timeseries.sepa.org.uk/KiWIS/KiWIS?service=kisters&type=queryServices&datasource=0&request=getTimeseriesValues'
    
    ts_id = row[4]
    
    full_record = None
    while full_record not in {'y','n'}:
        if full_record == None:
            full_record = input('\nDownload Full Period Of Record (Y/N) >> ').lower()
        else:
            print("\nresponse was not 'Y' or 'N'. Please try again")
            full_record = input('\nDownload Full Period Of Record (Y/N) >> ').lower()
    
    if full_record == 'y':
        
        date_from = dt.datetime.strptime(row[5], '%Y-%m-%dT%H:%M:%S.000Z')
        date_to = dt.datetime.strptime(row[6], '%Y-%m-%dT%H:%M:%S.000Z')
    
    if full_record == 'n':
        print('\nInput start and end dates in format DD-MM-YYYY')
        print('If start date is before period of record start the begining of the period of record will be used.')
        print('If end date is after period of record end the end of the period of record will be used.')
        
        date_from = dt.datetime.strptime(input("Type start date >> "), '%d-%m-%Y')
        date_to = dt.datetime.strptime(input("Type end date >> "), '%d-%m-%Y')
        
        if date_from <= dt.datetime.strptime(row[5], '%Y-%m-%dT%H:%M:%S.000Z'):
            date_from = dt.datetime.strptime(row[5], '%Y-%m-%dT%H:%M:%S.000Z')
        
        if date_to >= dt.datetime.strptime(row[6], '%Y-%m-%dT%H:%M:%S.000Z'):
            date_to = dt.datetime.strptime(row[6], '%Y-%m-%dT%H:%M:%S.000Z')
    
    station_details.append(date_from.strftime('%Y-%m-%dT%H:%M:%S.000Z'))  
    station_details.append(date_to.strftime('%Y-%m-%dT%H:%M:%S.000Z'))  
    
    ts = relativedelta(years=290000)
    if '15m' in row[3]:
        ts = dt.timedelta(seconds=15*60*290000)
    elif 'Hour' in row[3]:
        ts = dt.timedelta(seconds=1*3600*290000)
    elif 'Day' in row[3]:
        ts = dt.timedelta(seconds=24*3600*290000)
    elif 'Week' in row[3]:
        ts = dt.timedelta(seconds=7*24*3600*290000)
    elif 'Month' in row[3]:
        ts = relativedelta(months=290000)
    elif 'Year' in row[3] or 'Gaugings' in row[3] or 'POT' in row[3]:
        ts = relativedelta(years=290000)
    try:
        test = date_from + ts
    except ValueError:
        ts = relativedelta(years=9999-date_from.year)
        
    header_meta = [','.join(['Station Name',station_details[0]])]
    header_meta.append(','.join(['Station Number',station_details[1]]))
    header_meta.append(','.join(['Station Type',station_details[3]]))
    header_meta.append(','.join(['Station Easting',station_details[4]]))
    header_meta.append(','.join(['Station Northing',station_details[5]]))
    header_meta.append(','.join(['Station Parameter',station_details[6]]))
    header_meta.append(','.join(['Timeseries Name',station_details[7]]))
    header_meta.append(','.join(['Timestamp From',station_details[8]]))
    header_meta.append(','.join(['Timestamp To',station_details[9]]))
    
    print('\nDownloading Station Data Selected...\n')
    
    if date_to <= (date_from + ts):
        date_from = date_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        date_to = date_to.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        print(date_from, date_to)
        requestURL = '&'.join([base_url, 'ts_id=' + ts_id, 'from=' + date_from, 'to=' + date_to, 'returnfields=Timestamp,Value,Quality Code'])
        responseData = API_url_request(requestURL, accessKey, return_type='str', use_key=use_key)
    
    elif date_to > (date_from + ts):
        df = date_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        de = (date_from + ts).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        print(df, de)
        requestURL = '&'.join([base_url, 'ts_id=' + ts_id, 'from=' + df, 'to=' + de, 'returnfields=Timestamp,Value,Quality Code'])
        responseData = API_url_request(requestURL, accessKey, return_type='str', use_key=use_key)
        
        date_from = date_from + ts
        
        while date_to > (date_from + ts):
            df = date_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            de = (date_from + ts).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            print(df, de)
            requestURL = '&'.join([base_url, 'ts_id=' + ts_id, 'from=' + df, 'to=' + de, 'returnfields=Timestamp,Value,Quality Code'])
            responseData.extend(API_url_request(requestURL, accessKey, return_type='str', use_key=use_key)[3:])
            
            date_from = date_from + ts
            
        df = date_from.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        de = date_to.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        print(df, de)
        requestURL = '&'.join([base_url, 'ts_id=' + ts_id, 'from=' + df, 'to=' + de, 'returnfields=Timestamp,Value,Quality Code'])
        responseData.extend(API_url_request(requestURL, accessKey, return_type='str', use_key=use_key)[3:])    
    
    output_name = station_details[0] + '_' + station_details[1] + '_' + station_details[7] + '_' + station_details[6]    
    header_meta.extend(responseData)
    WriteCSV('\n'.join(header_meta) + '\n', output_folder='outputs', output_name=output_name)
    
    return output_name

#accessKeys = ['NjhjOTQxNzctNDY1NS00OWMzLWIyNWItMGExZTYwZTRlZTk0Ojg0ZmYzZmYxLTAwZGQtNDNjNS1hMDhjLTViOTUzOGJjNDRjYg==']        
count = 0
run_again = None
while run_again != 'n':
    use_key = None
    while use_key not in {'y','n'}:
        if use_key == None:
            use_key = input('\nUse Access Key (Y/N) >> ').lower()
        else:
            print("\nresponse was not 'Y' or 'N'. Please try again")
            use_key = input('\nUse Access Key (Y/N) >> ').lower()
    
    accessKey = ''
    if use_key == 'y':
        
        with open(r'authentication\accessKey.txt', 'r') as file:
            accessKey = file.read()
    
        print('\nAccess Key Read From File\n' + accessKey + '\n')
    
    output_name = SelectStation(accessKey, use_key)
    print('\nDonwload Complete - Check Output Folder!\nFile name >> ' + output_name + '.csv')

    run_again = None
    while run_again not in {'y','n'}:
        if run_again == None:
            run_again = input('\nDo you wish to download another dataset? (Y/N) >> ').lower()
        else:
            print("\nresponse was not 'Y' or 'N'. Please try again")
            run_again = input('\nUse Access Key (Y/N) >> ').lower()
    
        
print('\nExiting Program...')
time.sleep(2)