/*
If you don't want to follow the example below, here is the JDBC URI for you.
jdbc:postgresql://pg-3e00cdfd-seyon-0c3e.d.aivencloud.com:12186/defaultdb?ssl=require&user=avnadmin&password=<redacted>
*/


import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class PostgresqlExample {
    public static void main(String[] args) throws ClassNotFoundException {
        try (final Connection connection =
                    DriverManager.getConnection("jdbc:postgresql://pg-3e00cdfd-seyon-0c3e.d.aivencloud.com:12186/defaultdb?ssl=require&user=avnadmin&password=<redacted>");
            final Statement statement = connection.createStatement();
            final ResultSet resultSet = statement.executeQuery("SELECT version()")) {

        while (resultSet.next()) {
            System.out.println("Version: " + resultSet.getString("version"));
        }
        } catch (SQLException e) {
            System.out.println("Connection failure.");
            e.printStackTrace();
        }
    }
}