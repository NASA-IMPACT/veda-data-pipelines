// Example script for reconciling any files which might be missing from S3
// To use, first generate lists of:
// `s3Files` - list of files on S3 (this currently expects S3 files to be .tif files)
// `s3Urls` - list of expected files (this expects URLs to .he5 files)
// Modify as needed
//
// Use the output, missing-urls.txt, in a job (e.g. AWS Batch or AWS Lambda) to
// process missing files.
s3Files = fs.readFileSync('s3-files.txt', 'utf-8').split('\n')
s3Urls = fs.readFileSync('', 'utf-8').split('\n')
missingFiles = [];
s3Urls.forEach(url => {
  if (!s3Files.includes(url.split('/').pop().replace('he5', 'tif'))) {
    missingFiles.push(url)
  }
});
fs.writeFileSync('missing-urls.txt', missingFiles.join('\n'));
