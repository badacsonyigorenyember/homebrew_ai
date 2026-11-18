using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Data;

[Table("beer_style", Schema = "ref")]
public class BeerStyle
{
    [Column("id")]
    public long Id { get; init; }

    [Column("code")]
    public required string Code { get; init; }

    [Column("name")]
    public string? Name { get; init; }
}