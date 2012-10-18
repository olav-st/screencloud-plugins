function qb2String(qbytearray) {
  var result = "";
  for (var i = 0; i < qbytearray.length(); i++) {
    result += String.fromCharCode(qbytearray.at(i));
  }
  return result;
}
