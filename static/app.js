var finished = [false, false, false, false];

// candlestick charts: https://api.exchange.coinbase.com/products/BTC-EUR/candles?start=2015-08-14T12:39:00&end=2015-08-15T12:39:00&granularity=900

$(document).ready(function() {
	update();
	makeChart();
});

function update() {
	$('#updating').text('updating...');
	$.getJSON("/account", function(data) {
		$('#account_btc').text(data.btc.toFixed(4));
		$('#account_eur').text(data.eur.toFixed(2));
		$('#account_total_btc').text(data.total_btc.toFixed(4));
		$('#account_total_eur').text(data.total_eur.toFixed(2));

		$.getJSON("https://api.exchange.coinbase.com/products/BTC-EUR/ticker", function(data) {

			$('#last_trade_price').text(parseFloat(data.price).toFixed(2));
			$.getJSON("https://api.exchange.coinbase.com/products/BTC-EUR/stats", function(data) {
				$('#total_trade_volume').text(parseFloat(data.volume).toFixed(4));
				finish(0);
			}).fail(function(){finish(0);});

		}).fail(function(){finish(0);});

	}).fail(function(){finish(0);});

	$.getJSON("/trades", function(data) {
		$('#trades_balance_eur').text(data.balance_eur.toFixed(4));
		$('#trades_balance_btc').text(data.balance_btc.toFixed(4));
		$('#trades_volume_eur').text(data.volume_eur.toFixed(2));
		$('#trades_volume_btc').text(data.volume_btc.toFixed(4));

		$('#trades_balance_eur_day').text(data.balance_eur_day.toFixed(4));
		$('#trades_balance_btc_day').text(data.balance_btc_day.toFixed(4));
		$('#trades_volume_eur_day').text(data.volume_eur_day.toFixed(2));
		$('#trades_volume_btc_day').text(data.volume_btc_day.toFixed(4));
		$('#trades_count_day').text(data.trades_count_day);

		$('#trades').html(' ');
		for (i = 0; i < data.trades.length; i++) {
			$('#trades').append('<tr><td class="'+data.trades[i].side+'">'+data.trades[i].side.toUpperCase()+'</td><td>'+parseFloat(data.trades[i].price).toFixed(2)+'</td><td>'+formatSize(data.trades[i]['size'])+'</td><td>'+formatFee(parseFloat(data.trades[i].fee).toFixed(4))+'</td><td>'+formatAgo(data.trades[i]['created_at'])+'</td></tr>');
		}

		$('#trades_count').text(data.trades.length);

		finish(1);
	}).fail(function(){finish(1);});

	$.getJSON("/orderbook", function(data) {
		$('#orderbook_bids').html(" ");
		for(i = 0; i < data.bids.length; i++) {
			own = data.bids[i][3] ? parseFloat(data.bids[i][3]).toFixed(4) : "";
			$('#orderbook_bids').append('<tr><td>'+formatBid(data.bids[i][0])+'</td><td>'+formatSize(data.bids[i][1])+'</td><td>'+formatSize(own)+'</td></tr>')
		}
		$('#orderbook_asks').html(" ");
		for(i = 0; i < data.asks.length; i++) {
			own = data.asks[i][3] ? parseFloat(data.asks[i][3]).toFixed(4) : "";
			$('#orderbook_asks').append('<tr><td>'+formatBid(data.asks[i][0])+'</td><td>'+formatSize(data.asks[i][1])+'</td><td>'+formatSize(own)+'</td></tr>')
		}
		$('#spread').text((parseFloat(data.asks[0][0]) - parseFloat(data.bids[0][0])).toFixed(2));
		$('#mid').text(((parseFloat(data.asks[0][0]) + parseFloat(data.bids[0][0]))/2.0).toFixed(2));

		finish(2);
	}).fail(function(){finish(2);});

	$.getJSON("/orders", function(data) {
		$('#orders').html(' ');
		for (i = 0; i < data.orders.length; i++) {
			$('#orders').append('<tr><td class="'+data.orders[i].side+'">'+data.orders[i].side.toUpperCase()+'</td><td>'+parseFloat(data.orders[i].price).toFixed(2)+'</td><td>'+formatSize(data.orders[i]['size'])+'</td><td>'+formatSize(data.orders[i].filled_size)+'</td><td>'+formatAgo(data.orders[i]['created_at'])+'</td></tr>');
		}

		finish(3);
	}).fail(function(){finish(3);});

	$.getJSON("https://api.exchange.coinbase.com/products/BTC-EUR/trades", function(data) {
		$('#markettrades').html(' ');
		for (i = 0; i < data.length; i++) {
			$('#markettrades').append('<tr><td class="'+data[i].side+'">'+formatBid(data[i]['price'])+'</td><td>'+formatSize(data[i]['size'])+'</td><td>'+formatAgo(data[i]['time'])+'</td></tr>');
		}
	});
}

function formatFee(fee) {
	if (fee.toString() != "0.0000") {
		return "<span style='color:#ff683a'>" + fee + "</span>";
	}
	return "<span>" + fee + "</span>";
}

function formatBid(bid) {
	if (bid.toString().indexOf(".") == -1) {
		return bid.toString() + ".<span>00</span>";
	} else {
		bid = bid.toString().split(".");
		if (bid[1].length == 1) {
			return bid[0]+".<span>"+bid[1]+"0<span>";
		} else {
			return bid[0]+".<span>"+bid[1].substr(0,2)+"<span>";
		}
	}
}

function formatSize(size) {
	if (size.length == 0) {
		return '<span>-</span>';
	}
	if (size.toString().indexOf(".") == -1) {
		if (size.length == 1) {
			return "<span class='inv'>0</span>"+size+".<span>00000000</span>";
		} else {
			return size+".<span>00000000</span>";
		}
	} else {
		// remove trailing zeros
		size = size.toString();
		while (size.substr(-1) == 0) {
			size = size.substr(0,size.length-1);
		}
		size = size.toString().split(".");
		if (size[0].length == 1) {
			size[0] = "<span class='inv'>0</span>"+size[0];
		}
		if (size[1].length > 8) {
			size[1] = size[1].substr(0,5);
		}
		padding = 8 - size[1].length;
		if (padding > 0) {
			size[1] = size[1] + "<span>";
			for (j = 0; j < padding; j++) {
				size[1] = size[1] + "0";
			}
			size[1] = size[1] + "</span>";
		}
		return size[0]+"."+size[1];
	}
}

function formatAgo(timestring) {
	date = new Date(timestring);
	now = new Date();
	ago = (now - date)/1000.0; // no in seconds

	if (ago < 30) {
		return "now";
	} else if (ago < 3600) {
		return Math.round(ago/60) + "m";
	} else {
		return Math.round(ago/3600) + "h";
	}
}

function finish(i) {
	finished[i] = true;
	if (finished[0] && finished[1] && finished[2] && finished[3]) {
		$('#updating').text(' ');
		finished = [false, false, false, false];
		window.setTimeout(update, parseFloat($('#polling_interval').val()));
	}
 }

 function makeChart(){
 	end = new Date();
 	start = new Date();
 	start.setDate(start.getDate() - 2);

    $.getJSON('https://api.exchange.coinbase.com/products/BTC-EUR/candles?start='+start.toISOString()+'&end='+end.toISOString()+'&granularity=1800', function (data) {

		data.reverse();  
        
        // split the data set into ohlc and volume
        var ohlc = [],
            volume = [],
            dataLength = data.length,
            // set the allowed units for data grouping
            groupingUnits = [[
                'minute',                         // unit name
                [30,60]                             // allowed multiples
            ]],

            i = 0;

        for (i; i < dataLength; i += 1) {
            ohlc.push([  // 1low 2high 3open 4close
                parseInt(data[i][0])*1000, // the date
                data[i][3], // open
                data[i][2], // high
                data[i][1], // low
                data[i][4] // close
            ]);

            volume.push([
                parseInt(data[i][0])*1000, // the date
                data[i][5] // the volume
            ]);
        }


        // create the chart
        $('#chart').highcharts('StockChart', {

            chart: {
                backgroundColor:'#1d2b34',
                borderWidth: 0,
                plotBorderWidth: 0
            },
            
            plotOptions: {
              	candlestick: {
                    upColor: '#1d2b34',
                    color: '#ff683a',
                    lineColor: '#ff683a',
                    upLineColor: '#8cf563'
                },
                column: {
                    color: '#404c54'
                }
            },
            
            rangeSelector: {
                enabled:false
            },
            navigator: {
                enabled: false
            },
            scrollbar: {
                enabled: false
            },
            exporting: {
                enabled: false
            },
            
            xAxis: [{
                gridLineWidth:0,
                lineWidth:1,
                lineColor:'#26333c',
                tickColor:'#26333c',
                labels: {
                    style: {
                        color: '#404c54',
                        fontWeight: 'bold'
                    }
                }
            }, {
                gridLineWidth:0,
                lineWidth:0
            }],
                 

            yAxis: [{
                labels: {
                    align: 'left',
                    x: 5,
                    style: {
                        color: '#404c54',
                        fontWeight: 'bold'
                    }
                },
                offset: 0,
                lineWidth: 0,
                gridLineWidth:0
            }, {
                labels: {
                    enabled:false
                },
                top: '65%',
                height: '35%',
                lineWidth: 0,
                gridLineWidth:0
            }],

            series: [{
                type: 'column',
                name: 'Volume',
                data: volume,
                yAxis: 1,
                dataGrouping: {
                    units: groupingUnits
                }},{
                type: 'candlestick',
                name: 'BTC/EUR',
                data: ohlc,
                dataGrouping: {
                    units: groupingUnits
                }
            }
            ]
        });
		window.setTimeout(makeChart, parseFloat($('#polling_interval').val())*10);
    });
 }