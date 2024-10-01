//Prettify
$(function () {
	window.prettyPrint && prettyPrint();
});

//Tooltips
$(function () {
	$("[rel=\"tooltip\"]").tooltip({
		html: true
	});
});

$(function () {
	function filterPath(string) {
		return string.replace(/^\//, '')
			.replace(/(index|default).[a-zA-Z]{3,4}$/, '')
			.replace(/\/$/, '');
	}
	var locationPath = filterPath(location.pathname);

	$('a[href*="#"]').each(function () {
		var thisPath = filterPath(this.pathname) || locationPath;
		if (locationPath == thisPath && (location.hostname == this.hostname || !this.hostname) && this.hash.replace(/#/, '')) {
			var target = this.hash;
			if (target) {
				$(this).click(function (event) {
					event.preventDefault();
					history.replaceState(null, null, target);
					scrollTo(target, 400);
				});
			}
		}
	});

	$('*[data-show-target').each((_index, element) => {
		var target = $(element).attr('data-show-target');
		$(element).click(event => {
			event.preventDefault();
			history.replaceState(null, null, target);

			$(target).slideToggle(200);
			$(target + "-overlay").toggleClass("active");
		});
	});

	function scrollTo(id, duration) {
		const group = $(id);

		//calculate destination place
		if (group.length == 0) {
			return false;
		}

		group.slideDown(duration);
		$(id + "-overlay").addClass("active");

		var dest = group.offset().top;
		dest -= 100;
		dest = Math.min(dest, $(document).height() - $(window).height());
		dest = Math.max(dest, 0);

		//go to destination
		$('html,body').animate({
			scrollTop: dest
		}, duration, 'swing');

		group.addClass('shadowPulse');
		group.one('animationend', () => {
			group.removeClass('shadowPulse');
			// do something else...
		});

		hashTagActive = this.hash;
		return true;
	}

	if (window.location.hash.length > 0) {
		if (!scrollTo(window.location.hash, 0)) {
			// The user may have followed an old link.
			// Hashes for entities are usually on the format #entityName, #entityName2, #entityName3, etc.
			// So we try to strip any numeric suffix and try again.
			// This is also relevant if the documentation has changed from having all entities on the same page, to having separate overload pages.
			const hash = window.location.hash;
			const hashWithoutNumber = hash.replace(/\d+$/, '');
			console.log(`Failed to scroll to ${hash}, trying ${hashWithoutNumber}`);
			scrollTo(hashWithoutNumber, 0);
		}
	}

	window.onhashchange = function () {
		scrollTo(window.location.hash, 0);
	};

	const version = packageVersion;
	const branch = packageBranch;
	const isBeta = packageIsBeta;
	const versionData = JSON.parse(localStorage.getItem("lastVersionData"));
	const maxAgeSeconds = 60 * 10;
	const updateVersionInfo = data => {
		let html = "";
		let seenVersion = new Set();
		const pathParts = window.location.href.split("/");
		const page = pathParts[pathParts.length - 1];
		let latest = data.find(item => item.name == branch + (isBeta ? "_dev" : ""));
		if (latest.version !== version) {
			const el = document.createElement("template");
			el.innerHTML = `<a href='${documentation_collection_base_url}/${isBeta ? "beta" : "stable"}/${page}' class="btn btn-danger">View latest${isBeta ? " beta" : ""} version</a>`;
			document.getElementById("navbar-header").appendChild(el.content.firstChild);
		} else if (isBeta) {
			const el = document.createElement("template");
			el.innerHTML = `<a href='${documentation_collection_base_url}/stable/${page}' class="btn btn-warning">View latest non-beta version</a>`;
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
				spans += `<span class='version-badge'>beta</span>`;
			}
			html += `<li><a rel="nofollow" href='${documentation_collection_base_url}/${item.docs}/${page}'>${spans}</a></li>`;
		}
		document.getElementById("package-version-alternatives").innerHTML = html;
	};

	// Cache the data for a few minutes in local storage.
	// This makes the "View latest version" button show up much quicker.
	if (versionData != null && new Date().getTime() < new Date(versionData.date).getTime() + maxAgeSeconds * 1000) {
		updateVersionInfo(versionData.data);
	} else {
		fetch(documentation_collection_base_url + "/versions.php").then(r => r.json()).then(data => {
			localStorage.setItem("lastVersionData", JSON.stringify({
				date: new Date().toISOString(),
				data: data
			}));
			updateVersionInfo(data);
		});
	}
});

function loadData(callbackWhenDone) {
	fetch(pathToRoot + "search_data.json").then(response => response.json()).then(callbackWhenDone);
}

function assertEqual(a, b) {
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
	substringDistance(key, haystack) {
		var w = haystack.length + 1;
		var h = key.length + 1;

		var distArr = this.distArr;
		for (var i = 0; i <= key.length; i++) for (var j = 0; j <= haystack.length; j++) distArr[i * w + j] = 0;

		for (var i = 0; i <= key.length; i++) distArr[i * w] = i;

		// First characters (before substring starts) cost nothing
		for (var i = 0; i <= haystack.length; i++) distArr[i] = 0;

		for (var i = 1; i <= key.length; i++) {
			for (var j = 1; j <= haystack.length; j++) {
				if (key[i - 1] == haystack[j - 1]) {
					distArr[i * w + j] = distArr[(i - 1) * w + j - 1];
				} else {
					// Note, nested Min operations should be used because Mathf.Min(a, b, c) will allocate an array (slow)
					distArr[i * w + j] = Math.min(Math.min(
						distArr[(i - 1) * w + j] + 1, // Delete
						distArr[i * w + j - 1] + 1), // Insert
						distArr[(i - 1) * w + j - 1] + 1 // Substitute
					);
				}
			}
		}

		var mn = 100000;
		for (var i = 0; i < haystack.length + 1; i++) {
			mn = Math.min(distArr[key.length * w + i], mn);
		}
		return mn;
	}
}


$(function () {
	loadData(function (data) {
		if (data) {
			var index = elasticlunr();
			index.addField('name');
			index.addField('body');
			index.setRef('index');

			let isLoaded = false;

			const lazyLoad = () => {
				// Lazy-initialize the search index.
				// To avoid SEO penalties for high javascript CPU usage.
				if (!isLoaded) {
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
					isLoaded = true;
				}
			};

			/**
			 * The seach function manages the terms lookup and result display
			 */

			function search(selectFirst) {
				lazyLoad();

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
					var item = data[res[i].ref | 0];
					var lastDot = item.fullname.lastIndexOf(".");
					var score = 0;
					if (searchPartBeforeDot.length > 0) {
						if (lastDot != -1) {
							var beforeDot = item.fullname.substr(0, lastDot);
							score -= levenstein.substringDistance(searchPartBeforeDot.toLowerCase(), beforeDot.toLowerCase());
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
					score = 100 * score / item.boost;

					res2.push({
						item: item,
						score: score,
					});
				}

				res2.sort((a, b) => b.score - a.score);

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

				results = results.slice(0, 5);

				var html = "";
				for (var i = 0; i < results.length; i++) {
					var items = results[i];
					items.sort((a, b) => {
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
				$("#searchfield").keydown(function (e) {
					if (e.keyCode == downArrow) {
						$('#search-dropdown a').first().focus();
						e.preventDefault();
					}
				});

				$("#search-dropdown a").keydown(function (e) {
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
			$("#search").on("click", () => search(false));
			$("#searchfield").on("input", () => search(false));
			$("#searchform").on("submit", function (e) {
				e.preventDefault();
				search(true);
			});
			// Load when selected
			$("#searchfield").on("focus", () => {
				// Load after a short delay, to avoid causing visible stutter
				setTimeout(lazyLoad, 50);
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
