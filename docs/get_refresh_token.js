const { google } = require('googleapis');
const readline = require('readline');
require('dotenv-flow').config();

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  'urn:ietf:wg:oauth:2.0:oob' // Use for manual flow (out-of-band)
);

// Scopes define what you want access to
const SCOPES = [
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/calendar.events',
];

// Step 1: Generate the consent URL
const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  prompt: 'consent',
  scope: SCOPES,
});

console.log('\n🔗 Visit this URL in your browser:\n');
console.log(authUrl);
console.log('\n🔑 After authorizing, paste the code below:\n');

// Step 2: Wait for user to input the auth code
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question('Enter the authorization code here: ', async (code) => {
  try {
    const { tokens } = await oauth2Client.getToken(code);
    console.log('\n✅ Success! Here are your tokens:\n');
    console.log('Access Token:', tokens.access_token);
    console.log('Refresh Token:', tokens.refresh_token);
    console.log('\n📌 Save the refresh token in your .env:\n');
    console.log(`GOOGLE_REFRESH_TOKEN=${tokens.refresh_token}`);
  } catch (err) {
    console.error('❌ Error retrieving tokens:', err);
  } finally {
    rl.close();
  }
});

