function qb2String(qbytearray) {
  var result = "";
  for (var i = 0; i < qbytearray.length(); i++) {
    result += String.fromCharCode(qbytearray.at(i));
  }
  return result;
}
function isBlank(str) {
    return (!str || /^\s*$/.test(str));
}
function isEmpty(str) {
    return (!str || 0 === str.length);
}
function isBlankOrEmpty(str)
{
    return isBlank(str) || isEmpty(str);
}
