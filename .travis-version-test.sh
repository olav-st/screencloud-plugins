SHORTNAME=$1
if [ -z "$SHORTNAME" ]; then
	echo "No plugin shortname provided. Test failed!"
	exit 1
fi
echo "Testing version num of '$SHORTNAME':"
VERSION=$(xmllint --xpath '//metadata/version/text()' $SHORTNAME/metadata.xml)
LIST_VERSION=$(xmllint --xpath "plugins//plugin[shortname='$SHORTNAME']/version/text()" ./plugin-list.xml)
if [ "$VERSION" != "$LIST_VERSION" ]; then
	echo "$VERSION != $LIST_VERSION"
	echo "Test FAILED!"
	exit 1
else
	echo "$VERSION == $LIST_VERSION"
	echo "Test passed!"
fi