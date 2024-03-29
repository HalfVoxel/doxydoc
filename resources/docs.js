//Prettify
$(document).ready(function() {
	window.prettyPrint && prettyPrint()
});

//Tooltips
$(document).ready(function() {
	$("[rel=\"tooltip\"]").tooltip({
		html: true
	});
});

$(document).ready(function() {
	function filterPath(string) {
		return string.replace(/^\//, '')
			.replace(/(index|default).[a-zA-Z]{3,4}$/, '')
			.replace(/\/$/, '');
	}
	var locationPath = filterPath(location.pathname);

	$('a[href*=#]').each(function() {
		var thisPath = filterPath(this.pathname) || locationPath;
		if (locationPath == thisPath && (location.hostname == this.hostname || !this.hostname) && this.hash.replace(/#/, '')) {
			var target = this.hash;
			if (target) {
				$(this).click(function(event) {
					event.preventDefault();
					scrollTo(target, 400);
				});
			}
		}
	});

	function scrollTo(id, duration) {
		$(id).slideDown(duration);
		$(id + "-overlay").fadeIn(duration);

		//calculate destination place
		console.log($(id));
		var dest = $(id).offset().top;
		dest -= 100;
		dest = Math.min(dest, $(document).height() - $(window).height());
		dest = Math.max(dest, 0);

		//go to destination
		$('html,body').animate({
			scrollTop: dest
		}, duration, 'swing');

		$(id).addClass('shadowPulse');
		$(id).one('animationend', () => {
		    $(id).removeClass('shadowPulse');
		    // do something else...
		});

		hashTagActive = this.hash;
	}

	if (window.location.hash.length > 0) {
		console.log("Hash1: " + window.location.hash);
		//$(window.location.hash).toggle();
		scrollTo(window.location.hash, 0);
	}

	window.onhashchange = function() {
		console.log("Hash: " + window.location.hash);
		$(window.location.hash).toggle();
		$(window.location.hash + "-overlay").fadeToggle();
	};

	const version = packageVersion;
	const branch = packageBranch;
	const isBeta = packageIsBeta;
	fetch(documentation_collection_base_url + "/versions.php").then(r => r.json()).then(data => {
		let html = "";
		let seenVersion = new Set();
		const pathParts = window.location.href.split("/");
		const page = pathParts[pathParts.length - 1];
		let latest = data.find(item => item.name == branch);
		if (latest.version !== version) {
			const el = document.createElement("template");
			el.innerHTML = `<a href='${documentation_collection_base_url}/${isBeta ? "beta" : "stable"}/${page}' class="btn btn-danger">View latest version</a>`;
			document.getElementById("navbar-header").appendChild(el.content.firstChild);
		}
		for (let i = 0; i < data.length; i++) {
			if (data[i].docs === null) continue;
			if (seenVersion.has(data[i].version)) continue;
			seenVersion.add(data[i].version);
			var item = data[i];
			const date = new Date(item.lastUpdated);
			// Format date as YYYY-MM-DD
			const formattedDate = date.toISOString().split('T')[0];
			let spans = `<span class='item-version'>${item.version}</span><span class='item-date'>${formattedDate}</span>`;
			if (item.name.includes("_dev")) {
				spans += `<span class='version-badge'>beta</span>`
			}
			html += `<li><a rel="nofollow" href='${documentation_collection_base_url}/${item.docs}/${page}'>${spans}</a></li>`;
		}
		document.getElementById("package-version-alternatives").innerHTML = html;
	});
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
			index.addField('body');
			index.setRef('index');

			for (var i = 0; i < data.length; i++) {
				const item = data[i];
				let body = "";
				for (var j = 0; j < item.keys.length; j++) {
					body += item.keys[j] + " ";
				}

				index.addDoc({
					name: item.name,
					index: i,
					body: body,
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

					const nameDistance = levenstein.substringDistance(searchPart.toLowerCase(), item.name.toLowerCase());

					let bestKeyword = 10;
					for (var j = 0; j < item.keys.length; j++) {
						const keyword = item.keys[j];
						bestKeyword = Math.min(bestKeyword, levenstein.substringDistance(searchPart.toLowerCase(), keyword.toLowerCase()));
					}
					bestKeyword = Math.min(bestKeyword, nameDistance);
					score -= 0.5 * bestKeyword;

					score -= nameDistance;
					// Break ties on length
					score -= 0.001 * item.fullname.length;
					score = 100*score/item.boost;
					console.log(item);

					res2.push({
						item: item,
						score: score,
					});
				}

				res2.sort((a,b) => b.score - a.score);

				// Re-sort
				//res.sort(function (a, b) { return b.score - a.score; });

				var t1 = performance.now();
				var name2index = {};
				var results = [];
				for (var i = 0; i < res2.length; i++) {
					var item = res2[i].item;//data[res[i].ref|0];
					if (!name2index.hasOwnProperty(item.name)) {
						name2index[item.name] = results.length;
						results.push([]);
					}
					results[name2index[item.name]].push({
						item: item,
						score: res2[i].score
					});
				}

				results = results.slice(0,5);

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

					var id = 'search_' + items[0].item.name.replace(/ /g, "_");

					if (items.length == 1) {
						let icon = "";
						if (items[0].item.type == "page") icon = "<span class='glyphicon glyphicon-book'></span>";

						html += "<li><a id='" + id + "_0' href='" + pathToRoot + items[0].item.url + "'>" + icon + items[0].item.name + "</a></li>";
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

				var upArrow = 38;
				var downArrow = 40;
				$("#search-dropdown").html(html);
				$("#search-dropdown").show(0);
				$("#searchfield").keydown(function(e) {
					if (e.keyCode == downArrow) {
						$('#search-dropdown a').first().focus();
						e.preventDefault();
					}
				});

				$("#search-dropdown a").keydown(function(e) {
					if (e.keyCode == downArrow || e.keyCode == upArrow) {
						var selector = $('#search-dropdown a:visible');
						var index = selector.index(this);

						if (e.keyCode == downArrow) index++;
						else if (e.keyCode == upArrow) index--;

						if (index == -1) {
							$("#searchfield").focus();
						} else {
							var next = selector.eq(index);
							next.focus();
						}
						e.preventDefault();
					}
				});

				if (selectFirst && results.length > 0) {
					var id = 'search_' + results[0][0].item.name.replace(/ /g, "_");
					$("#" + id).show(0);
					$('#search-dropdown a').first().focus();
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
				// Select the search field when pressing 'f'
				if (document.activeElement != "INPUT" && e.keyCode == 70) {
					$("#searchfield").focus();
					e.preventDefault();
				}
			}
			// register the handler 
			document.addEventListener('keyup', onKeyUp, false);
		} else {
			console.log("Can't load a file");
		}
	});
});
