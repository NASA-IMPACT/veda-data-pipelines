s3Files = fs.readFileSync('', 'utf-8').split('\n')
s3Urls = fs.readFileSync('', 'utf-8').split('\n')
missingFiles = [];
s3Urls.forEach(url => {
  if (!s3Files.includes(url.split('/').pop().replace('he5', 'tif'))) {
    missingFiles.push(url)
  }
});
fs.writeFileSync('missing-omi-urls.txt', missingFiles.join('\n'));
