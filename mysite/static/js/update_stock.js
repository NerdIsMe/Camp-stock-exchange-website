function refreshAt(hours, minutes, seconds) {
    var now = new Date();
    var then = new Date();

    if(now.getHours() > hours ||
    (now.getHours() == hours && now.getMinutes() > minutes) ||
        now.getHours() == hours && now.getMinutes() == minutes && now.getSeconds() >= seconds) {
        then.setDate(now.getDate() + 1);
    }
    then.setHours(hours);
    then.setMinutes(minutes);
    then.setSeconds(seconds);

    var timeout = (then.getTime() - now.getTime());
    setTimeout(function() { window.location.reload(true); }, timeout);

}

var date = new Date();
date.yyyymmdd();
function startTime() {
var today = new Date();
var y = today.getFullYear();
var mon = (today.getMonth()+1);
var d = today.getDate();
var h = today.getHours();
var m = today.getMinutes();
var s = today.getSeconds();
mon = checkTime(mon),
d = checkTime(d);
m = checkTime(m);
s = checkTime(s);
document.getElementById('txt').innerHTML = 
y +'/' + mon +'/'+ d+ ' ' + h + ":" + m + ":" + s;

var t = setTimeout(startTime, 500);
}
function checkTime(i) {
if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
return i;
}
