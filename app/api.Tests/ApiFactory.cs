using DotNet.Testcontainers.Builders;

using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;

using Npgsql;

using Testcontainers.PostgreSql;

namespace HomebrewApp.Tests;

public class ApiFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    public string AppApiConnectionString =>
        new NpgsqlConnectionStringBuilder(_container.GetConnectionString())
        {
            Username = "app_api",
            Password = _password
        }.ConnectionString;

    private const string _password = "dummy_password";

    private readonly PostgreSqlContainer _container =
        new PostgreSqlBuilder("supabase/postgres:15.8.1.085")
            .WithUsername("supabase_admin")
            .WithCommand("-c", "config_file=/etc/postgresql/postgresql.conf")
            .WithResourceMapping(
                DirectoryPath.Of(Path.Combine(CommonDirectoryPath.GetGitDirectory().DirectoryPath, "db")),
                DirectoryPath.Of("/db/"))
            .WithResourceMapping(
                DirectoryPath.Of(Path.Combine(CommonDirectoryPath.GetProjectDirectory().DirectoryPath, "TestData")),
                DirectoryPath.Of("/seed/"))
            .Build();

    public async Task InitializeAsync()
    {
        await _container.StartAsync();

        // ref.beer_style and ref.ingredient (Recipe.Style, RecipeItem.Ingredient).
        await RunSqlFileAsync("/db/010_ref_schema.sql");
        // Schema app, the pg_jsonschema extension, app.recipe (with process) and app.recipe_item.
        await RunSqlFileAsync("/db/015_app.sql");
        // The app_api login role and its grants; the password is a psql variable, as on the stack.
        await RunSqlFileAsync("/db/060_app_api_role.sql", "app_api_password=" + _password);

        var seed = await File.ReadAllTextAsync(Path.Combine(CommonDirectoryPath.GetProjectDirectory().DirectoryPath,
            "TestData/recipe-1155-process.json"));
        await RunSqlFileAsync("/seed/seed.sql", "process=" + seed);
    }

    async Task IAsyncLifetime.DisposeAsync()
    {
        await _container.DisposeAsync();
        await base.DisposeAsync();
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseSetting("ConnectionStrings:App", AppApiConnectionString);
    }

    private async Task RunSqlFileAsync(string pathInContainer, params string[] variables)
    {
        var command = new List<string>
        {
            "psql",
            "-U",
            "postgres",
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            $"{pathInContainer}"
        };

        foreach (var variable in variables)
        {
            command.Add("-v");
            command.Add(variable);
        }

        var result = await _container.ExecAsync(command);

        if (result.ExitCode != 0)
        {
            throw new InvalidOperationException($"{pathInContainer} failed with error: {result.Stderr}");
        }
    }
}
