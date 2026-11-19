using Npgsql;

namespace HomebrewApp.Tests.Database;

[Collection(nameof(ApiCollection))]
public class AppApiRoleTests(ApiFactory factory)
{
    [Fact]
    public async Task AppApi_SelectRecipes_ReturnsSeededRows()
    {
        await using var conn = new NpgsqlConnection(factory.AppApiConnectionString);
        await conn.OpenAsync();

        await using var command = new NpgsqlCommand("select COUNT(*) from app.recipe", conn);
        var result = await command.ExecuteScalarAsync();

        Assert.Equal(2L, result);
    }

    [Fact]
    public async Task AppApi_UpdateRecipes_IsRefused()
    {
        await using var conn = new NpgsqlConnection(factory.AppApiConnectionString);
        await conn.OpenAsync();

        await using var command = new NpgsqlCommand("update app.recipe set status = status where false", conn);
        var exception = await Assert.ThrowsAsync<PostgresException>(async () => await command.ExecuteScalarAsync());

        Assert.Equal(PostgresErrorCodes.InsufficientPrivilege, exception.SqlState);
    }
}
