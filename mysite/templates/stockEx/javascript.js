//var date = new Date();
//date.yyyymmdd();

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