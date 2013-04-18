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


var searchData = [];

/**
 * Loads the data (the csv file containing the color data)
 * @param callbackWhenDone function called when loaded
 */

function loadData(callbackWhenDone) {
	var loader = new fullproof.DataLoader();
	loader.setQueue("searchdata.csv");
	loader.start(fullproof.make_callback(callbackWhenDone, true),

	function(txt) {
		searchData = txt.split("\n");
	}, fullproof.make_callback(callbackWhenDone, false));
}

/**
 * The initializer is a function called by the engine when the index
 * is created for the first time. It provides an opportunity to populate
 * the index with its data.
 * @param {fullproof.TextInjector} injector an object of type fullproof.TextInjector
 * @param callback function function to call when the initialization is done
 */

function initializer(injector, callback) {
	var processData = function() {

		var values = [];
		var textData = [];
		for (var i = 0; i < searchData.length; ++i) {
			var texts = searchData[i].split("|$|");
			if (texts) {

				if (texts[1] != undefined) {
					//Name
					values.push(i);
					textData.push(texts[1] + " " + texts[2] + " " + texts[4]);
				}

				// Desc
				//values.push(i);
				//textData.push(texts[2]);
			}
		}
		var synchro = fullproof.make_synchro_point(callback, textData.length - 1);

		console.log(textData.length + " " + values.length + " " + searchData.length)
		injector.injectBulk(textData, values, callback);
	};

	if (searchData.length == 0) {
		loadData(function(b)  {
			if (b) {
				processData()
			} else {
				alert("Can't load a file");
			}
		});
	} else {
		processData();
	}
}

/**
 * This function get called when the engine is done opening itself
 * @param b true if the engine was successfully open, false otherwise
 */

function engineReady(b) {
}

$(document).ready(function() {

	// window.installInlineConsole("debug");

	var dbName = "doxysearch";
	//		var onlyMem = [new fullproof.StoreDescriptor("memorystore", fullproof.store.IndexedDBStore)];
	// onlyMem
	var docSearchEngine = new fullproof.ScoringEngine();

	// Loads the color data from the csv, then creates the index descriptors and uses them to open the indexes
	loadData(function() {
		/*var index1 = {
						name: "normalindex",
						analyzer: new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.normalizer.remove_duplicate_letters),
						capabilities: new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
						initializer: initializer
				};
				var index2 = {
						name: "stemmedindex",
						analyzer: new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.metaphone),
						capabilities: new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
						initializer: initializer
				};*/

		var index1 = new fullproof.IndexUnit("normalindex",
		new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8 * 1024 * 1024),
		new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.normalizer.remove_duplicate_letters),
		initializer);

		var index2 = new fullproof.IndexUnit("stemmedindex",
		new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8 * 1024 * 1024),
		new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.metaphone),
		initializer);
		docSearchEngine.open([index1, index2], fullproof.make_callback(engineReady, true), fullproof.make_callback(engineReady, false));
	});

	/**
	 * The seach function manages the terms lookup and result display
	 */

	function search() {
		var value = $("#searchfield").val();

		console.log("Searching")

		if (value == "reload") {
			docSearchEngine.clear(function() {
				window.location.reload(true);
			});
		}

		// Request a search to the colorSearchEengine, then displays the results, if any.
		docSearchEngine.lookup(value, function(resultset) {
			var result = "";
			if (resultset && resultset.getSize()) {

				resultset.setComparatorObject({
					lower_than: function(a, b)  {
						return a.score > b.score;
					},
					equals: function(a, b) {
						return a.score === b.score;
					}
				});
				if (docSearchEngine.lastResultIndex == 1) {
					//result = "<h1>Found " + resultset.getSize() + " color"+(resultset.getSize()>1?"s":"")+" matching your request.</h1>";
				} else {
					//result = "<h1>No match for '" + value + "', but found " + resultset.getSize() + " approximate match"+(resultset.getSize()>1?"es":"")+".</h1>";
				}

				//result += "<table><tr><th>Color Name</th><th>Sample</th><th>Hex Code</th></tr>"
				resultset.forEach(function(e) {
					if (e instanceof fullproof.ScoredElement) {
						console.log(e);
						var c = searchData[e.value].split("|$|");
					} else {
						var c = searchData[e].split("|$|");
					}
					result += "<li>";
					result += "<a href='" + c[0] + "'>";
					if (c[4] != undefined && c[4] != "") result += "<small>" + c[4] + "</small>&nbsp;"
					if (c[3] != undefined && c[3] != "") result += c[3] + "&nbsp;"
					result += "<b>" + c[1] + "</b>";

					desc = c[2]
					if (desc != undefined && desc.length > 0) {
						maxlen = desc.indexOf("<")
						if (maxlen < 0) maxlen = 30
						maxlen = Math.min(desc.length, maxlen)

						desc2 = desc.substring(0, maxlen)
						if (desc2.length != desc.length) desc2 = desc2 + "..."

						result += "&nbsp;<small>" + desc2 + "</small></a>";
					} else {
						result += "</a>"
					}
					result += "</li>";
				});
				//result += "</table>";
			} else {
				result = "<li>No results found</li>";
			}
			$("#search-dropdown").html(result);
			//$("#search-dropdown").dropdown();
			//$('.dropdown-toggle').dropdown();
			$('#search-dropdown').show(0);
		});
	}

	// Bind the search action
	$("#search").click(search);
	$("#searchfield").change(search);
	$("#searchform").submit(function(e) {
		e.preventDefault();
	});
	//$("#search-dropdown").click(function(e) { e.stopPropagation(); });
	//$("body").click(function(e) { $('#search-dropdown').hide(0); });
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