Generates daily email notifications for various digital assets at daily close (00:00) UTC. First version is centered around bitcoin/crypto.

Users subscribe via Google Form (not currently public), and user data is accessed via the Sheety API (https://sheety.co). Users are given options as to which digital assets they would like to be notified about.
Cryptocurrency data is accessed via the CoinGecko API (https://www.coingecko.com/en/api).

Returns price, % change, and total market cap. Have other data organized but looks too busy with too much, wanted to keep it simple initially but may add more customizable notifications later.

Service is automated via python anywhere (https://www.pythonanywhere.com).

Functionalities to be added:
- Additional usage of a stock market API to utilize data on main indices, and so users can compare/contrast price changes between asset classes and correlations/divergences.
- More options (custom options?) as to which assets users want to be notified of
- Customization in types/amount of data user receives
- Addition of more functions to clean code of repetition (in progress)
- Inspirational Quotes? (haha)
- Possibly more intermediate techniques in the future i.e. incorporate a hash map to simulate a significantly larger userbase.



This is my first personal project with the goals of generating all code/ideas myself and completing the first rendition before a month of beginning my coding journey. 
