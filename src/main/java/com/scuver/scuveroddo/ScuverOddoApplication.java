package com.scuver.scuveroddo;

import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.net.URL;
import java.util.HashMap;
import java.util.Map;

import static java.util.Arrays.asList;
import static java.util.Collections.emptyList;
import static java.util.Collections.emptyMap;

@SpringBootApplication
@RestController
public class ScuverOddoApplication {

	public static void main(String[] args) throws Exception{

		final XmlRpcClient client = new XmlRpcClient();

//		final XmlRpcClientConfigImpl start_config = new XmlRpcClientConfigImpl();
//		start_config.setServerURL(new URL("http://localhost:8069"));
//		final Map<String, String> info = (Map<String, String>)client.execute(
//				start_config, "start", emptyList());

//		final String url = info.get("host"),
//				db = info.get("database"),
//				username = info.get("user"),
//				password = info.get("password");
//
//		String[] config =  new String[]{url, db, username, password};
//
//		System.out.println(config);

		final String url = "http://localhost:8069",
		db = "scuver-test",
		username = "scuverpt@gmail.com",
		password = "tmp12345";

		final XmlRpcClientConfigImpl common_config = new XmlRpcClientConfigImpl();
		common_config.setServerURL(new URL(String.format("%s/xmlrpc/2/common", "http://localhost:8069")));
//
		System.out.println("Authentication result: " + client.execute(common_config, "authenticate", asList(db, username, password, emptyMap())));

		int uid = (int)client.execute(common_config, "authenticate", asList(db, username, password, emptyMap()));

		final XmlRpcClient models = new XmlRpcClient() {{
			setConfig(new XmlRpcClientConfigImpl() {{
				setServerURL(new URL(String.format("%s/xmlrpc/2/object", url)));
			}});
		}};

		System.out.println(asList((Object[])models.execute("execute_kw", asList(
				db, uid, password,
				"pos.order", "search",
				asList(asList())
		))));

		System.out.println(asList((Object[])models.execute("execute_kw", asList(
				db, uid, password,
				"pos.order.line", "search",
				asList(asList())
		))));

		int orderId = (int)models.execute("execute_kw", asList(
				db, uid, password,
				"pos.order", "create",
				asList(new HashMap() {{
					put("name", "Shop/0005");
					put("company_id", 1);
					// put("date_order", "2022-10-31 11:12:09.355000");
					put("user_id", 2);
					put("session_id", 4);
					put("amount_total", 33);
					put("amount_tax", 0);
					put("amount_paid", 33);
					put("amount_return", 0);
					put("pricelist_id", 2);
					put("location_id", 16);
					put("pos_reference", "Order 00001-001-0001");
					put("sale_journal", "1");
					put("state", "paid");
				}})
		));

		System.out.println(models.execute("execute_kw", asList(
				db, uid, password,
				"pos.order.line", "create",
				asList(new HashMap() {{
					put("company_id", 1);
					put("name", "Shop/0018");
					put("product_id", 20);
					put("price_unit", 16.5);
					put("qty", 2);
					put("price_subtotal", 33);
					put("price_subtotal_incl", 33);
					put("order_id", orderId);
				}})
		)));

		// SpringApplication.run(ScuverOddoApplication.class, args);
	}

//	@GetMapping("/test")
//	public Object login(@RequestParam(value = "domain", defaultValue = "https://demo.odoo.com/start") String domain) throws Exception{
//
//		final XmlRpcClient client = new XmlRpcClient();
//
//		final XmlRpcClientConfigImpl start_config = new XmlRpcClientConfigImpl();
//		start_config.setServerURL(new URL(domain));
//		final Map<String, String> info = (Map<String, String>)client.execute(
//				start_config, "start", emptyList());
//
//		final String url = info.get("host"),
//				db = info.get("database"),
//				username = info.get("user"),
//				password = info.get("password");
//
//		final XmlRpcClientConfigImpl common_config = new XmlRpcClientConfigImpl();
//		common_config.setServerURL(new URL(String.format("%s/xmlrpc/2/common", url)));
//
//		String[] config =  new String[]{url, db, username, password};
//
//		client.execute(common_config, "version", emptyList());
//
//		int uid = (int)client.execute(common_config, "authenticate", asList(db, username, password, emptyMap()));
//
//		final XmlRpcClient models = new XmlRpcClient() {{
//			setConfig(new XmlRpcClientConfigImpl() {{
//				setServerURL(new URL(String.format("%s/xmlrpc/2/object", url)));
//			}});
//		}};
//
//		return models.execute("execute_kw", asList(
//				db, uid, password,
//				"res.partner", "check_access_rights",
//				asList("read"),
//				new HashMap() {{ put("raise_exception", false); }}
//		));
//	}
}
