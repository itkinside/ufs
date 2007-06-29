// Fixes support for our drop-down menu in IE
// Taken from http://www.alistapart.com/articles/dropdowns/
function menulist() {
    if (document.all && document.getElementById) {
        navRoot = document.getElementById("menulist");
        for (i=0; i<navRoot.childNodes.length; i++) {
            node = navRoot.childNodes[i];
            if (node.nodeName=="LI") {
                node.onmouseover=function() {
                    this.className+=" over";
                }
                node.onmouseout=function() {
                    this.className=this.className.replace(" over", "");
                }
            }
        }
    }
}
