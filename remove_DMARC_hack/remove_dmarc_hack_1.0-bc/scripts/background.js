browser.compose.onBeforeSend.addListener((tab, details) => {
    /*console.log(details);
    console.log("details.plainText of just after onBeforeSend: ", details.plainTextBody);
    console.log("original to:", details.to);
    console.log("original cc:", details.cc);
    console.log("original bcc:", details.bcc);*/
    stripDMARChack(details.to);
    stripDMARChack(details.cc);
    stripDMARChack(details.bcc);
    /*console.log("stripped");
    console.log("stripped to:", details.to);
    console.log("stripped cc:", details.cc);
    console.log("stripped bcc:", details.bcc);*/
    browser.compose.setComposeDetails(tab.id, {to: details.to, cc: details.cc, bcc: details.bcc}).then(() => {
        console.log("tabId: " + tab.id + " setComposeDetails finished.");
    });
    browser.compose.getComposeDetails(tab.id).then((d) => {
        console.log("details of after setComposeDetails: ", d);
    });
    return;
});

function stripDMARChack(addresses) {
    for (let i = 0; i < addresses.length; i++) {
        if (addresses[i].includes('@dmarc.ietf.org')) {
            addresses[i] = addresses[i].replace('@dmarc.ietf.org', '').replace('=40', '@');
        }
    }
    return; // addresses;
}
