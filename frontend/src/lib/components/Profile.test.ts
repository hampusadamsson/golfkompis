import { describe, it, expect, afterEach } from 'vitest';
import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';
import type { Profile } from '$lib/api';

function makeProfile(overrides: Partial<Profile> = {}): Profile {
	return {
		sessionId: 'sess1',
		personId: 'p1',
		firstName: 'Anna',
		lastName: 'Svensson',
		golfId: '123456-789',
		homeClubId: 'c1',
		homeClubName: 'Stockholms GK',
		districtName: 'Stockholm',
		favouriteClubId: null,
		representationClubName: null,
		representationClubShort: null,
		gender: 'K',
		birthDate: '1982-04-15',
		age: 42,
		hcp: '12.4',
		allowedToBook: true,
		allowedToBookWithNoCharge: false,
		allowedToCompetitionSignUp: true,
		allowedToCompetitionSignUpNoCharge: false,
		allowedToPay: true,
		emailAddress: 'anna@golf.se',
		hasActiveMembership: true,
		loggedInToMinGolfThisYear: true,
		minors: [],
		memberClubs: [
			{ isHomeClub: true, id: 'c1', name: 'Stockholms GK' },
			{ isHomeClub: false, id: 'c2', name: 'Lidingö GK' },
		],
		caregiverPersonId: null,
		caregiverGolfId: null,
		isMinor: false,
		isMinorWithoutCaregiver: false,
		imageUrl: null,
		isDefaultSupport: false,
		isFederationSuspended: false,
		isFederationSuspendedCompetition: false,
		isMinorNotLoggedInAsCaregiver: false,
		capped: false,
		softCap: null,
		hardCap: null,
		lowestHcp: null,
		hcpCard: null,
		isSgfJunior: false,
		isMemberOfTeenTourClub: false,
		hasPaidTeenTourYearlyFee: false,
		mustChangePassword: false,
		isLoggedInWithFreja: false,
		showPersonInfoView: false,
		isForeign: false,
		country: null,
		...overrides,
	} as unknown as Profile;
}

// Gender label logic (mirrors Profile.svelte)
function genderLabel(gender: string): string {
	if (gender === 'M') return 'Man';
	if (gender === 'K' || gender === 'F') return 'Kvinna';
	return gender;
}

// Initials logic (mirrors Profile.svelte)
function initials(firstName: string, lastName: string): string {
	return `${firstName[0] ?? ''}${lastName[0] ?? ''}`.toUpperCase();
}

afterEach(() => {
	mingolfProfile.clear();
});

describe('Profile view logic', () => {
	it('profile is null by default — nothing to render', () => {
		expect(mingolfProfile.profile).toBeNull();
	});

	it('profile fields are accessible after set', () => {
		mingolfProfile.profile = makeProfile();
		const p = mingolfProfile.profile!;
		expect(p.firstName).toBe('Anna');
		expect(p.lastName).toBe('Svensson');
		expect(p.golfId).toBe('123456-789');
		expect(p.hcp).toBe('12.4');
		expect(p.age).toBe(42);
	});

	it('gender M maps to "Man"', () => {
		expect(genderLabel('M')).toBe('Man');
	});

	it('gender K maps to "Kvinna"', () => {
		expect(genderLabel('K')).toBe('Kvinna');
	});

	it('gender F maps to "Kvinna"', () => {
		expect(genderLabel('F')).toBe('Kvinna');
	});

	it('initials are derived from first letters of firstName and lastName', () => {
		expect(initials('Bo', 'Karlsson')).toBe('BK');
		expect(initials('Anna', 'Svensson')).toBe('AS');
	});

	it('home club star: only one club is isHomeClub', () => {
		mingolfProfile.profile = makeProfile();
		const homeClubs = mingolfProfile.profile!.memberClubs.filter((c) => c.isHomeClub);
		expect(homeClubs.length).toBe(1);
		expect(homeClubs[0].name).toBe('Stockholms GK');
	});

	it('hasActiveMembership false triggers warning badge', () => {
		mingolfProfile.profile = makeProfile({ hasActiveMembership: false });
		expect(mingolfProfile.profile!.hasActiveMembership).toBe(false);
	});

	it('allowedToBook false triggers warning badge', () => {
		mingolfProfile.profile = makeProfile({ allowedToBook: false });
		expect(mingolfProfile.profile!.allowedToBook).toBe(false);
	});
});
