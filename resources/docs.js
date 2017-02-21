//Tooltips
$(document).ready(function() {
	$("[rel=\"tooltip\"]").tooltip({
		html: true
	});
});

//Prettify
$(document).ready(function() {
	window.prettyPrint && prettyPrint()
});

$(document).ready(function() {
	window.onhashchange = function() {
		console.log("Here...");
		$(window.location.hash).toggle();
	};
});

function loadData(callbackWhenDone) {
	$.getJSON(pathToRoot + "search_data.json", callbackWhenDone);
}

function assertEqual(a,b) {
	if (a !== b) {
		console.log("Assertion failed " + a + " " + b);
	}
}

class Levenstein {
	constructor() {
		this.distArr = [];

		assertEqual(this.substringDistance("a", "aaa"), 0);
		assertEqual(this.substringDistance("b", "aaa"), 1);
		assertEqual(this.substringDistance("abc", "aaabcccc"), 0);
		assertEqual(this.substringDistance("abc", "qqqabcqqq"), 0);
		assertEqual(this.substringDistance("abc", "cba"), 2);   // 2 insertions
		assertEqual(this.substringDistance("aabbcc", "qqaabbdd"), 2);   // 2 insertions
		assertEqual(this.substringDistance("aabbcc", "qqqaaqq"), 4);   // 4 insertions
		assertEqual(this.substringDistance("abc", "aqbqc"), 2);   // 2 deletions
		assertEqual(this.substringDistance("abc", "qaqbqcq"), 2);   // 2 deletions
		assertEqual(this.substringDistance("a", "b"), 1);   // 1 insertion
		assertEqual(this.substringDistance("abc", "blahadcblah"), 1);   // 1 substitution
		assertEqual(this.substringDistance("aaaaaa", "a"), 5);   // 5 insertions
		assertEqual(this.substringDistance("aaaaaa", "b"), 6);   // 6 insertions
	}

	/* Compute the distance between key and any substring in haystack */
	substringDistance (key, haystack) {
		var w = haystack.length+1;
		var h = key.length+1;

		var distArr = this.distArr;
		for (var i = 0; i <= key.length; i++) for (var j = 0; j <= haystack.length; j++) distArr[i*w + j] = 0;

		for (var i = 0; i <= key.length; i++) distArr[i*w] = i;

		// First characters (before substring starts) cost nothing
		for (var i = 0; i <= haystack.length; i++) distArr[i] = 0;

		for (var i = 1; i <= key.length; i++) {
			for (var j = 1; j <= haystack.length; j++) {
				if (key[i-1] == haystack[j-1]) {
					distArr[i*w + j] = distArr[(i-1)*w + j-1];
				} else {
					// Note, nested Min operations should be used because Mathf.Min(a, b, c) will allocate an array (slow)
					distArr[i*w + j] = Math.min(Math.min(
							distArr[(i-1)*w + j] + 1, // Delete
							distArr[i*w + j-1] + 1), // Insert
						distArr[(i-1)*w + j-1] + 1 // Substitute
					);
				}
			}
		}

		var mn = 100000;
		for (var i = 0; i < haystack.length+1; i++) {
			mn = Math.min(distArr[key.length*w + i], mn);
		}
		return mn;
	}
}


$(document).ready(function() {
	loadData(function(data)  {
		if (data) {
			var index = elasticlunr();
			index.addField('name');
			index.setRef('index');

			for (var i = 0; i < data.length; i++) {
				index.addDoc({
					name: data[i].name,
					index: i
				});
			}

			/**
			 * The seach function manages the terms lookup and result display
			 */

			function search(selectFirst) {
				var value = $("#searchfield").val().trim();

				var parts = value.split(".");
				var searchPartBeforeDot = parts.slice(0, parts.length - 1).join(".").trim();
				var searchPart = parts[parts.length - 1];
				// Request a search to the colorSearchEengine, then displays the results, if any.
				var res = index.search(searchPart, {
					expand: true
				});

				var levenstein = new Levenstein();
				var res2 = [];
				for (var i = 0; i < res.length; i++) {
					var item = data[res[i].ref|0];
					var lastDot = item.fullname.lastIndexOf(".");
					var score = 0;
					if (searchPartBeforeDot.length > 0) {
						if (lastDot != -1) {
							var beforeDot = item.fullname.substr(0, lastDot);
							score -= levenstein.substringDistance(searchPartBeforeDot.toLowerCase(), beforeDot.toLowerCase())
						} else {
							score -= 10;
						}
					}

					score -= levenstein.substringDistance(searchPart.toLowerCase(), item.name.toLowerCase());
					// Break ties on length
					score -= 0.001 * item.fullname.length;
					score = 100*score/item.boost;

					res2.push({
						item: item,
						score: score,
					});
				}

				res2.sort((a,b) => b.score - a.score);
				console.log(res2);

				// Re-sort
				//res.sort(function (a, b) { return b.score - a.score; });

				var t1 = performance.now();
				var name2index = {};
				var results = [];
				for (var i = 0; i < res2.length; i++) {
					var item = res2[i].item;//data[res[i].ref|0];
					if (!(item.name in name2index)) {
						name2index[item.name] = results.length;
						results.push([]);
					}
					results[name2index[item.name]].push({
						item: item,
						score: res2[i].score
					});
				}

				results = results.slice(0,5);
				console.log(results);

				var html = "";
				for (var i = 0; i < results.length; i++) {
					var items = results[i];
					items.sort((a,b) => {
						if (b.score > a.score) return 1;
						else if (b.score < a.score) return -1;

						var pa = a.item.fullname.split(".")[0];
						var pb = b.item.fullname.split(".")[0];
						return pa.length - pb.length;
					});

					var id = 'search_' + items[0].item.name.replace(" ", "_");

					if (items.length == 1) {
						html += "<li><a id='" + id + "_0' href='" + pathToRoot + items[0].item.url + "'>" + items[0].item.name + "</a></li>";
					} else {
						html += '<li><a href="#" onclick="$(\'#' + id + '\').toggle(0);">' + items[0].item.name + " ...</a></li>";
						html += "<ul class='inner-dropdown-menu' id='" + id + "' style='display: none;'>";
						for (var j = 0; j < items.length; j++) {
							var inner = items[j].item;
							var lastDot = inner.fullname.lastIndexOf(".");
							var beforeDot = lastDot != -1 ? inner.fullname.substr(0, lastDot) : "";
							var afterDot = lastDot != -1 ? inner.fullname.substr(lastDot + 1) : inner.fullname;
							html += "<li><a id='" + id + "_" + j + "' href='" + pathToRoot + inner.url + "'><span>" + afterDot + "</span><small>" + beforeDot + "</small></a></li>";
						}
						html += "</ul>";
					}
				}
				$("#search-dropdown").html(html);
				$("#search-dropdown").show(0);

				if (selectFirst && results.length > 0) {
					var id = 'search_' + results[0][0].item.name.replace(" ", "_");
					$("#" + id).show(0);
					$("#" + id + "_0").focus();
				}
			}

			// Bind the search action
			$("#search").click(() => search(false));
			$("#searchfield").on("input", () => search(false));
			$("#searchform").submit(function(e) {
				e.preventDefault();
				search(true);
			});


			// define a handler
			function onKeyUp(e) {
				if (document.activeElement != "INPUT" && e.keyCode == 70) {
				    $("#searchfield").focus();
				}
			}
			// register the handler 
			document.addEventListener('keyup', onKeyUp, false);
		} else {
			console.log("Can't load a file");
		}
	});
});


//Smooth Scrolling
$(document).ready(function() {
	function filterPath(string) {
		return string.replace(/^\//, '')
			.replace(/(index|default).[a-zA-Z]{3,4}$/, '')
			.replace(/\/$/, '');
	}
	var locationPath = filterPath(location.pathname);
	var scrollElem = scrollableElement('html', 'body');

	$('a[href*=#]').each(function() {
		var thisPath = filterPath(this.pathname) || locationPath;
		if (locationPath == thisPath && (location.hostname == this.hostname || !this.hostname) && this.hash.replace(/#/, '')) {
			var $target = $(this.hash),
				target = this.hash;
			if (target) {
				var targetOffset = $target.offset().top;
				$(this).click(function(event) {
					event.preventDefault();
					$(scrollElem).animate({
						scrollTop: targetOffset
					}, 400, 'swing', function() {
						location.hash = target;
						/*$(target).prop('id',target.substr(1)+'-noscroll');
						console.log ($target.prop("id"));
						console.log ($(target));
						console.log ($target);
						window.location.hash = target;
						console.log (target);
						$(target).prop('id',target.substr(1)); */
					});
				});
			}
		}
	});

	// use the first element that is "scrollable"

	function scrollableElement(els) {
		for (var i = 0, argLength = arguments.length; i < argLength; i++) {
			var el = arguments[i],
				$scrollElement = $(el);
			if ($scrollElement.scrollTop() > 0) {
				return el;
			} else {
				$scrollElement.scrollTop(1);
				var isScrollable = $scrollElement.scrollTop() > 0;
				$scrollElement.scrollTop(0);
				if (isScrollable) {
					return el;
				}
			}
		}
		return [];
	}

});
